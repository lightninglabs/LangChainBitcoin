from base64 import standard_b64encode, standard_b64decode

from nacl.secret import SecretBox

from pymacaroons.field_encryptors.base_field_encryptor import (
    BaseFieldEncryptor
)
from pymacaroons.utils import (
    truncate_or_pad, convert_to_bytes, convert_to_string
)


class SecretBoxEncryptor(BaseFieldEncryptor):

    def __init__(self, signifier=None, nonce=None):
        super(SecretBoxEncryptor, self).__init__(
            signifier=signifier or 'sbe::'
        )
        self.nonce = nonce

    def encrypt(self, signature, field_data):
        encrypt_key = truncate_or_pad(signature)
        box = SecretBox(key=encrypt_key)
        encrypted = box.encrypt(convert_to_bytes(field_data), nonce=self.nonce)
        return self._signifier + standard_b64encode(encrypted)

    def decrypt(self, signature, field_data):
        key = truncate_or_pad(signature)
        box = SecretBox(key=key)
        encoded = convert_to_bytes(field_data[len(self.signifier):])
        decrypted = box.decrypt(standard_b64decode(encoded))
        return convert_to_string(decrypted)
