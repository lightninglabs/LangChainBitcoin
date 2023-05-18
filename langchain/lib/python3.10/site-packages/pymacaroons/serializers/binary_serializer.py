from __future__ import unicode_literals

import binascii
from collections import namedtuple
import six
import struct
import sys
from base64 import urlsafe_b64encode

from pymacaroons.utils import (
    convert_to_bytes,
    convert_to_string,
    raw_b64decode,
)
from pymacaroons.serializers.base_serializer import BaseSerializer
from pymacaroons.exceptions import MacaroonSerializationException


PacketV2 = namedtuple('PacketV2', ['field_type', 'data'])


class BinarySerializer(BaseSerializer):

    PACKET_PREFIX_LENGTH = 4
    _LOCATION = 1
    _IDENTIFIER = 2
    _VID = 4
    _SIGNATURE = 6
    _EOS = 0

    def serialize(self, macaroon):
        return urlsafe_b64encode(
            self.serialize_raw(macaroon)).decode('ascii').rstrip('=')

    def serialize_raw(self, macaroon):
        from pymacaroons.macaroon import MACAROON_V1
        if macaroon.version == MACAROON_V1:
            return self._serialize_v1(macaroon)
        return self._serialize_v2(macaroon)

    def _serialize_v1(self, macaroon):
        combined = self._packetize(b'location', macaroon.location)
        combined += self._packetize(b'identifier', macaroon.identifier)

        for caveat in macaroon.caveats:
            combined += self._packetize(b'cid', caveat._caveat_id)

            if caveat._verification_key_id and caveat._location:
                combined += self._packetize(
                    b'vid', caveat._verification_key_id)
                combined += self._packetize(b'cl', caveat._location)

        combined += self._packetize(
            b'signature',
            binascii.unhexlify(macaroon.signature_bytes)
        )
        return combined

    def _serialize_v2(self, macaroon):
        from pymacaroons.macaroon import MACAROON_V2

        # https://github.com/rescrv/libmacaroons/blob/master/doc/format.txt
        data = bytearray()
        data.append(MACAROON_V2)
        if macaroon.location is not None:
            self._append_packet(data, self._LOCATION, convert_to_bytes(
                macaroon.location))
            self._append_packet(data, self._IDENTIFIER,
                                macaroon.identifier_bytes)
        self._append_packet(data, self._EOS)
        for c in macaroon.caveats:
            if c.location is not None:
                self._append_packet(data, self._LOCATION,
                                    convert_to_bytes(c.location))
            self._append_packet(data, self._IDENTIFIER, c.caveat_id_bytes)
            if c.verification_key_id is not None:
                self._append_packet(data, self._VID, convert_to_bytes(
                    c.verification_key_id))
            self._append_packet(data, self._EOS)
        self._append_packet(data, self._EOS)
        self._append_packet(data, self._SIGNATURE, binascii.unhexlify(
            macaroon.signature_bytes))
        return bytes(data)

    def deserialize(self, serialized):
        if len(serialized) == 0:
            raise ValueError('empty macaroon')
        serialized = convert_to_string(serialized)
        decoded = raw_b64decode(serialized)
        return self.deserialize_raw(decoded)

    def deserialize_raw(self, serialized):
        from pymacaroons.macaroon import MACAROON_V2
        from pymacaroons.exceptions import MacaroonDeserializationException

        first = six.byte2int(serialized[:1])
        if first == MACAROON_V2:
            return self._deserialize_v2(serialized)
        if _is_ascii_hex(first):
            return self._deserialize_v1(serialized)
        raise MacaroonDeserializationException(
            'cannot determine data format of binary-encoded macaroon')

    def _deserialize_v1(self, decoded):
        from pymacaroons.macaroon import Macaroon, MACAROON_V1
        from pymacaroons.caveat import Caveat
        from pymacaroons.exceptions import MacaroonDeserializationException

        macaroon = Macaroon(version=MACAROON_V1)

        index = 0

        while index < len(decoded):
            packet_length = int(
                struct.unpack(
                    b"4s",
                    decoded[index:index + self.PACKET_PREFIX_LENGTH]
                )[0],
                16
            )
            packet = decoded[
                index + self.PACKET_PREFIX_LENGTH:index + packet_length
            ]

            key, value = self._depacketize(packet)

            if key == b'location':
                macaroon.location = value
            elif key == b'identifier':
                macaroon.identifier = value
            elif key == b'cid':
                macaroon.caveats.append(Caveat(caveat_id=value,
                                               version=MACAROON_V1))
            elif key == b'vid':
                macaroon.caveats[-1].verification_key_id = value
            elif key == b'cl':
                macaroon.caveats[-1].location = value
            elif key == b'signature':
                macaroon.signature = binascii.hexlify(value)
            else:
                raise MacaroonDeserializationException(
                    'Key {key} not valid key for this format. '
                    'Value: {value}'.format(
                        key=key, value=value
                    )
                )

            index = index + packet_length

        return macaroon

    def _deserialize_v2(self, serialized):
        from pymacaroons.macaroon import Macaroon, MACAROON_V2
        from pymacaroons.caveat import Caveat
        from pymacaroons.exceptions import MacaroonDeserializationException

        # skip the initial version byte.
        serialized = serialized[1:]
        serialized, section = self._parse_section_v2(serialized)
        loc = ''
        if len(section) > 0 and section[0].field_type == self._LOCATION:
            loc = section[0].data.decode('utf-8')
            section = section[1:]
        if len(section) != 1 or section[0].field_type != self._IDENTIFIER:
            raise MacaroonDeserializationException('invalid macaroon header')
        macaroon = Macaroon(
            identifier=section[0].data,
            location=loc,
            version=MACAROON_V2,
        )
        while True:
            rest, section = self._parse_section_v2(serialized)
            serialized = rest
            if len(section) == 0:
                break
            cav = Caveat(version=MACAROON_V2)
            if len(section) > 0 and section[0].field_type == self._LOCATION:
                cav.location = section[0].data.decode('utf-8')
                section = section[1:]

            if len(section) == 0 or section[0].field_type != self._IDENTIFIER:
                raise MacaroonDeserializationException(
                    'no identifier in caveat')

            cav.caveat_id = section[0].data
            section = section[1:]
            if len(section) == 0:
                # First party caveat.
                if cav.location is not None:
                    raise MacaroonDeserializationException(
                        'location not allowed in first party caveat')
                macaroon.caveats.append(cav)
                continue

            if len(section) != 1:
                raise MacaroonDeserializationException(
                    'extra fields found in caveat')

            if section[0].field_type != self._VID:
                raise MacaroonDeserializationException(
                    'invalid field found in caveat')
            cav.verification_key_id = section[0].data
            macaroon.caveats.append(cav)
        serialized, packet = self._parse_packet_v2(serialized)
        if packet.field_type != self._SIGNATURE:
            raise MacaroonDeserializationException(
                'unexpected field found instead of signature')
        macaroon.signature = binascii.hexlify(packet.data)
        return macaroon

    def _packetize(self, key, data):
        # The 2 covers the space and the newline
        packet_size = self.PACKET_PREFIX_LENGTH + 2 + len(key) + len(data)
        # Ignore the first two chars, 0x
        packet_size_hex = hex(packet_size)[2:]

        if packet_size > 65535:
            raise MacaroonSerializationException(
                'Packet too long for serialization. '
                'Max length is 0xFFFF (65535). '
                'Packet length: 0x{hex_length} ({length}) '
                'Key: {key}'.format(
                    key=key,
                    hex_length=packet_size_hex,
                    length=packet_size
                )
            )

        header = packet_size_hex.zfill(4).encode('ascii')
        packet_content = key + b' ' + convert_to_bytes(data) + b'\n'
        packet = struct.pack(
            convert_to_bytes("4s%ds" % len(packet_content)),
            header,
            packet_content
        )
        return packet

    def _depacketize(self, packet):
        key = packet.split(b' ')[0]
        value = packet[len(key) + 1:-1]
        return (key, value)

    def _append_packet(self, data, field_type, packet_data=None):
        _encode_uvarint(data, field_type)
        if field_type != self._EOS:
            _encode_uvarint(data, len(packet_data))
            data.extend(packet_data)

    def _parse_section_v2(self, data):
        ''' Parses a sequence of packets in data.

        The sequence is terminated by a packet with a field type of EOS
        :param data bytes to be deserialized.
        :return: the rest of data and an array of packet V2
        '''

        from pymacaroons.exceptions import MacaroonDeserializationException

        prev_field_type = -1
        packets = []
        while True:
            if len(data) == 0:
                raise MacaroonDeserializationException(
                    'section extends past end of buffer')
            rest, packet = self._parse_packet_v2(data)
            if packet.field_type == self._EOS:
                return rest, packets
            if packet.field_type <= prev_field_type:
                raise MacaroonDeserializationException('fields out of order')
            packets.append(packet)
            prev_field_type = packet.field_type
            data = rest

    def _parse_packet_v2(self, data):
        ''' Parses a V2 data packet at the start of the given data.

        The format of a packet is as follows:

        field_type(varint) payload_len(varint) data[payload_len bytes]

        apart from EOS which has no payload_en or data (it's a single zero
        byte).

        :param data:
        :return: rest of data, PacketV2
        '''
        from pymacaroons.exceptions import MacaroonDeserializationException

        ft, n = _decode_uvarint(data)
        data = data[n:]
        if ft == self._EOS:
            return data, PacketV2(ft, None)
        payload_len, n = _decode_uvarint(data)
        data = data[n:]
        if payload_len > len(data):
            raise MacaroonDeserializationException(
                'field data extends past end of buffer')
        return data[payload_len:], PacketV2(ft, data[0:payload_len])


def _encode_uvarint(data, n):
    ''' Encodes integer into variable-length format into data.'''
    if n < 0:
        raise ValueError('only support positive integer')
    while True:
        this_byte = n & 0x7f
        n >>= 7
        if n == 0:
            data.append(this_byte)
            break
        data.append(this_byte | 0x80)


if sys.version_info.major == 2:
    def _decode_uvarint(data):
        ''' Decode a variable -length integer.

        Reads a sequence of unsigned integer byte and decodes them into an
        integer in variable-length format and returns it and the length read.
        '''
        n = 0
        shift = 0
        i = 0
        for b in data:
            b = ord(b)
            i += 1
            if b < 0x80:
                return n | b << shift, i
            n |= (b & 0x7f) << shift
            shift += 7
        raise Exception('cannot read uvarint from buffer')
else:
    def _decode_uvarint(data):
        ''' Decode a variable -length integer.

        Reads a sequence of unsigned integer byte and decodes them into an
        integer in variable-length format and returns it and the length read.
        '''
        n = 0
        shift = 0
        i = 0
        for b in data:
            i += 1
            if b < 0x80:
                return n | b << shift, i
            n |= (b & 0x7f) << shift
            shift += 7
        raise Exception('cannot read uvarint from buffer')


def _is_ascii_hex(b):
    if ord('0') <= b <= ord('9'):
        return True
    if ord('a') <= b <= ord('f'):
        return True
    return False
