import binascii

from pymacaroons.binders.base_binder import BaseBinder
from pymacaroons.utils import hmac_concat, truncate_or_pad


class HashSignaturesBinder(BaseBinder):

    def __init__(self, root, key=None):
        super(HashSignaturesBinder, self).__init__(root)
        self.key = key or truncate_or_pad(b'\0')

    def bind_signature(self, signature):
        return hmac_concat(
            self.key,
            binascii.unhexlify(self.root.signature_bytes),
            binascii.unhexlify(signature)
        )
