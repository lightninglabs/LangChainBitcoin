from __future__ import unicode_literals
import binascii

from pymacaroons import Caveat
from pymacaroons.utils import (
    convert_to_string,
    convert_to_bytes,
    sign_first_party_caveat
)

from .base_first_party import (
    BaseFirstPartyCaveatDelegate,
    BaseFirstPartyCaveatVerifierDelegate
)


class FirstPartyCaveatDelegate(BaseFirstPartyCaveatDelegate):

    def __init__(self, *args, **kwargs):
        super(FirstPartyCaveatDelegate, self).__init__(*args, **kwargs)

    def add_first_party_caveat(self, macaroon, predicate, **kwargs):
        predicate = convert_to_bytes(predicate)
        # Check it's valid utf-8 for first party caveats.
        # Will raise a unicode error if not.
        predicate.decode('utf-8')
        caveat = Caveat(caveat_id=predicate, version=macaroon.version)
        macaroon.caveats.append(caveat)
        encode_key = binascii.unhexlify(macaroon.signature_bytes)
        macaroon.signature = sign_first_party_caveat(encode_key, predicate)
        return macaroon


class FirstPartyCaveatVerifierDelegate(BaseFirstPartyCaveatVerifierDelegate):

    def __init__(self, *args, **kwargs):
        super(FirstPartyCaveatVerifierDelegate, self).__init__(*args, **kwargs)

    def verify_first_party_caveat(self, verifier, caveat, signature):
        predicate = convert_to_string(caveat.caveat_id)
        caveat_met = sum(callback(predicate)
                         for callback in verifier.callbacks)
        return caveat_met

    def update_signature(self, signature, caveat):
        return binascii.unhexlify(
            sign_first_party_caveat(
                signature,
                caveat.caveat_id_bytes
            )
        )
