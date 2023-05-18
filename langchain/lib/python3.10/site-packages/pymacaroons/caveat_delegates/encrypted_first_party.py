from __future__ import unicode_literals
import binascii

from six import iteritems
from pymacaroons.field_encryptors import SecretBoxEncryptor

from .first_party import (
    FirstPartyCaveatDelegate, FirstPartyCaveatVerifierDelegate
)


class EncryptedFirstPartyCaveatDelegate(FirstPartyCaveatDelegate):

    def __init__(self, field_encryptor=None, *args, **kwargs):
        self.field_encryptor = field_encryptor or SecretBoxEncryptor()
        super(EncryptedFirstPartyCaveatDelegate, self).__init__(
            *args, **kwargs
        )

    def add_first_party_caveat(self, macaroon, predicate, **kwargs):
        if kwargs.get('encrypted'):
            predicate = self.field_encryptor.encrypt(
                binascii.unhexlify(macaroon.signature_bytes),
                predicate
            )
        return super(EncryptedFirstPartyCaveatDelegate,
                     self).add_first_party_caveat(macaroon,
                                                  predicate,
                                                  **kwargs)


class EncryptedFirstPartyCaveatVerifierDelegate(
        FirstPartyCaveatVerifierDelegate):

    def __init__(self, field_encryptors=None, *args, **kwargs):
        secret_box_encryptor = SecretBoxEncryptor()
        self.field_encryptors = dict(
            (f.signifier, f) for f in field_encryptors
        ) if field_encryptors else {
            secret_box_encryptor.signifier: secret_box_encryptor
        }
        super(EncryptedFirstPartyCaveatVerifierDelegate, self).__init__(
            *args, **kwargs
        )

    def verify_first_party_caveat(self, verifier, caveat, signature):
        predicate = caveat.caveat_id_bytes

        for signifier, encryptor in iteritems(self.field_encryptors):
            if predicate.startswith(signifier):
                predicate = encryptor.decrypt(
                    signature,
                    predicate
                )

        caveat_met = sum(callback(predicate)
                         for callback in verifier.callbacks)
        return caveat_met
