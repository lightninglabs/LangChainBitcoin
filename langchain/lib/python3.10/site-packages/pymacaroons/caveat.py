from base64 import standard_b64encode

from pymacaroons.utils import convert_to_string, convert_to_bytes


class Caveat(object):

    def __init__(self,
                 caveat_id=None,
                 verification_key_id=None,
                 location=None,
                 version=None):
        from pymacaroons.macaroon import MACAROON_V1
        self.caveat_id = caveat_id
        self.verification_key_id = verification_key_id
        self.location = location
        if version is None:
            version = MACAROON_V1
        self._version = version

    @property
    def caveat_id(self):
        from pymacaroons.macaroon import MACAROON_V1
        if self._version == MACAROON_V1:
            return convert_to_string(self._caveat_id)
        return self._caveat_id

    @property
    def caveat_id_bytes(self):
        return self._caveat_id

    @property
    def verification_key_id(self):
        return self._verification_key_id

    @property
    def location(self):
        return convert_to_string(self._location)

    @caveat_id.setter
    def caveat_id(self, value):
        self._caveat_id = convert_to_bytes(value)

    @verification_key_id.setter
    def verification_key_id(self, value):
        self._verification_key_id = convert_to_bytes(value)

    @location.setter
    def location(self, value):
        self._location = convert_to_bytes(value)

    def first_party(self):
        return self._verification_key_id is None

    def third_party(self):
        return self._verification_key_id is not None

    def to_dict(self):
        try:
            cid = convert_to_string(self.caveat_id)
        except UnicodeEncodeError:
            cid = convert_to_string(standard_b64encode(self.caveat_id_bytes))
        return {
            'cid': cid,
            'vid': (
                standard_b64encode(self.verification_key_id)
                if self.verification_key_id else None
            ),
            'cl': self.location
        }
