from pymacaroons.utils import convert_to_bytes


class BaseFieldEncryptor(object):

    def __init__(self, signifier=None, nonce=None):
        self.signifier = signifier or ''
        self.nonce = nonce

    @property
    def signifier(self):
        return convert_to_bytes(self._signifier)

    @signifier.setter
    def signifier(self, string_or_bytes):
        self._signifier = convert_to_bytes(string_or_bytes)

    def encrypt(self, signature, field_data):
        raise NotImplementedError()

    def decrypt(self, signature, field_data):
        raise NotImplementedError()
