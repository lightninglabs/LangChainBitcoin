import base64
from hashlib import sha256
import hmac
import binascii

from six import text_type, binary_type


def convert_to_bytes(string_or_bytes):
    if string_or_bytes is None:
        return None
    if isinstance(string_or_bytes, text_type):
        return string_or_bytes.encode('utf-8')
    elif isinstance(string_or_bytes, binary_type):
        return string_or_bytes
    else:
        raise TypeError("Must be a string or bytes object.")


def convert_to_string(string_or_bytes):
    if string_or_bytes is None:
        return None
    if isinstance(string_or_bytes, text_type):
        return string_or_bytes
    elif isinstance(string_or_bytes, binary_type):
        return string_or_bytes.decode('utf-8')
    else:
        raise TypeError("Must be a string or bytes object.")


def truncate_or_pad(byte_string, size=None):
    if size is None:
        size = 32
    byte_array = bytearray(byte_string)
    length = len(byte_array)
    if length > size:
        return bytes(byte_array[:size])
    elif length < size:
        return bytes(byte_array + b"\0"*(size-length))
    else:
        return byte_string


def generate_derived_key(key):
    return hmac_digest(b'macaroons-key-generator', key)


def hmac_digest(key, data):
    return hmac.new(
        key,
        msg=data,
        digestmod=sha256
    ).digest()


def hmac_hex(key, data):
    dig = hmac_digest(key, data)
    return binascii.hexlify(dig)


def create_initial_signature(key, identifier):
    derived_key = generate_derived_key(key)
    return hmac_hex(derived_key, identifier)


def hmac_concat(key, data1, data2):
    hash1 = hmac_digest(key, data1)
    hash2 = hmac_digest(key, data2)
    return hmac_hex(key, hash1 + hash2)


def sign_first_party_caveat(signature, predicate):
    return hmac_hex(signature, predicate)


def sign_third_party_caveat(signature, verification_id, caveat_id):
    return hmac_concat(signature, verification_id, caveat_id)


def equals(val1, val2):
    """
    Returns True if the two strings are equal, False otherwise.

    The time taken is independent of the number of characters that match.

    For the sake of simplicity, this function executes in constant time only
    when the two strings have the same length. It short-circuits when they
    have different lengths.
    """
    if len(val1) != len(val2):
        return False
    result = 0
    for x, y in zip(val1, val2):
        result |= ord(x) ^ ord(y)
    return result == 0


def add_base64_padding(b):
    '''Add padding to base64 encoded bytes.

    Padding can be removed when sending the messages.

    @param b bytes to be padded.
    @return a padded bytes.
    '''
    return b + b'=' * (-len(b) % 4)


def raw_b64decode(s):
    if '_' or '-' in s:
        return raw_urlsafe_b64decode(s)
    else:
        return base64.b64decode(add_base64_padding(s))


def raw_urlsafe_b64decode(s):
    '''Base64 decode with added padding and conversion to bytes.

    @param s string decode
    @return bytes decoded
    '''
    return base64.urlsafe_b64decode(add_base64_padding(s.encode('utf-8')))


def raw_urlsafe_b64encode(b):
    '''Base64 encode with padding removed.

    @param s string decode
    @return bytes decoded
    '''
    return base64.urlsafe_b64encode(b).rstrip(b'=')
