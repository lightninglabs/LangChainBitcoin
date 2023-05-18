import binascii
import json
from pymacaroons import utils


class JsonSerializer(object):
    '''Serializer used to produce JSON macaroon format v1.
    '''
    def serialize(self, m):
        '''Serialize the macaroon in JSON format indicated by the version field.

        @param macaroon the macaroon to serialize.
        @return JSON macaroon.
        '''
        from pymacaroons import macaroon
        if m.version == macaroon.MACAROON_V1:
            return self._serialize_v1(m)
        return self._serialize_v2(m)

    def _serialize_v1(self, macaroon):
        '''Serialize the macaroon in JSON format v1.

        @param macaroon the macaroon to serialize.
        @return JSON macaroon.
        '''
        serialized = {
            'identifier': utils.convert_to_string(macaroon.identifier),
            'signature': macaroon.signature,
        }
        if macaroon.location:
            serialized['location'] = macaroon.location
        if macaroon.caveats:
            serialized['caveats'] = [
                _caveat_v1_to_dict(caveat) for caveat in macaroon.caveats
            ]
        return json.dumps(serialized)

    def _serialize_v2(self, macaroon):
        '''Serialize the macaroon in JSON format v2.

        @param macaroon the macaroon to serialize.
        @return JSON macaroon in v2 format.
        '''
        serialized = {}
        _add_json_binary_field(macaroon.identifier_bytes, serialized, 'i')
        _add_json_binary_field(binascii.unhexlify(macaroon.signature_bytes),
                               serialized, 's')

        if macaroon.location:
            serialized['l'] = macaroon.location
        if macaroon.caveats:
            serialized['c'] = [
                _caveat_v2_to_dict(caveat) for caveat in macaroon.caveats
            ]
        return json.dumps(serialized)

    def deserialize(self, serialized):
        '''Deserialize a JSON macaroon depending on the format.

        @param serialized the macaroon in JSON format.
        @return the macaroon object.
        '''
        deserialized = json.loads(serialized)
        if deserialized.get('identifier') is None:
            return self._deserialize_v2(deserialized)
        else:
            return self._deserialize_v1(deserialized)

    def _deserialize_v1(self, deserialized):
        '''Deserialize a JSON macaroon in v1 format.

        @param serialized the macaroon in v1 JSON format.
        @return the macaroon object.
        '''
        from pymacaroons.macaroon import Macaroon, MACAROON_V1
        from pymacaroons.caveat import Caveat

        caveats = []
        for c in deserialized.get('caveats', []):
            caveat = Caveat(
                caveat_id=c['cid'],
                verification_key_id=(
                    utils.raw_b64decode(c['vid']) if c.get('vid')
                    else None
                ),
                location=(
                    c['cl'] if c.get('cl') else None
                ),
                version=MACAROON_V1
            )
            caveats.append(caveat)

        return Macaroon(
            location=deserialized.get('location'),
            identifier=deserialized['identifier'],
            caveats=caveats,
            signature=deserialized['signature'],
            version=MACAROON_V1
        )

    def _deserialize_v2(self, deserialized):
        '''Deserialize a JSON macaroon v2.

        @param serialized the macaroon in JSON format v2.
        @return the macaroon object.
        '''
        from pymacaroons.macaroon import Macaroon, MACAROON_V2
        from pymacaroons.caveat import Caveat
        caveats = []
        for c in deserialized.get('c', []):
            caveat = Caveat(
                caveat_id=_read_json_binary_field(c, 'i'),
                verification_key_id=_read_json_binary_field(c, 'v'),
                location=_read_json_binary_field(c, 'l'),
                version=MACAROON_V2
            )
            caveats.append(caveat)
        return Macaroon(
            location=_read_json_binary_field(deserialized, 'l'),
            identifier=_read_json_binary_field(deserialized, 'i'),
            caveats=caveats,
            signature=binascii.hexlify(
                _read_json_binary_field(deserialized, 's')),
            version=MACAROON_V2
        )


def _caveat_v1_to_dict(c):
    ''' Return a caveat as a dictionary for export as the JSON
    macaroon v1 format.
    '''
    serialized = {}
    if len(c.caveat_id) > 0:
        serialized['cid'] = c.caveat_id
    if c.verification_key_id:
        serialized['vid'] = utils.raw_urlsafe_b64encode(
            c.verification_key_id).decode('utf-8')
    if c.location:
        serialized['cl'] = c.location
    return serialized


def _caveat_v2_to_dict(c):
    ''' Return a caveat as a dictionary for export as the JSON
    macaroon v2 format.
    '''
    serialized = {}
    if len(c.caveat_id_bytes) > 0:
        _add_json_binary_field(c.caveat_id_bytes, serialized, 'i')
    if c.verification_key_id:
        _add_json_binary_field(c.verification_key_id, serialized, 'v')
    if c.location:
        serialized['l'] = c.location
    return serialized


def _add_json_binary_field(b, serialized, field):
    ''' Set the given field to the given val (a bytearray) in the serialized
    dictionary.

    If the value isn't valid utf-8, we base64 encode it and use field+"64"
    as the field name.
    '''
    try:
        val = b.decode("utf-8")
        serialized[field] = val
    except UnicodeDecodeError:
        val = utils.raw_urlsafe_b64encode(b).decode('utf-8')
        serialized[field + '64'] = val


def _read_json_binary_field(deserialized, field):
    ''' Read the value of a JSON field that may be string or base64-encoded.
    '''
    val = deserialized.get(field)
    if val is not None:
        return utils.convert_to_bytes(val)
    val = deserialized.get(field + '64')
    if val is None:
        return None
    return utils.raw_urlsafe_b64decode(val)
