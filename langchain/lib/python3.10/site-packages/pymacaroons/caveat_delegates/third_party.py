from __future__ import unicode_literals
import binascii

from nacl.secret import SecretBox

from pymacaroons import Caveat
from pymacaroons.utils import (
    convert_to_bytes,
    truncate_or_pad,
    generate_derived_key,
    sign_third_party_caveat,
)
from pymacaroons.exceptions import MacaroonUnmetCaveatException
from .base_third_party import (
    BaseThirdPartyCaveatDelegate,
    BaseThirdPartyCaveatVerifierDelegate,
)


class ThirdPartyCaveatDelegate(BaseThirdPartyCaveatDelegate):

    def __init__(self, *args, **kwargs):
        super(ThirdPartyCaveatDelegate, self).__init__(*args, **kwargs)

    def add_third_party_caveat(self,
                               macaroon,
                               location,
                               key,
                               key_id,
                               **kwargs):
        derived_key = truncate_or_pad(
            generate_derived_key(convert_to_bytes(key))
        )
        old_key = truncate_or_pad(binascii.unhexlify(macaroon.signature_bytes))
        box = SecretBox(key=old_key)
        verification_key_id = box.encrypt(
            derived_key, nonce=kwargs.get('nonce')
        )
        caveat = Caveat(
            caveat_id=key_id,
            location=location,
            verification_key_id=verification_key_id,
            version=macaroon.version
        )
        macaroon.caveats.append(caveat)
        encode_key = binascii.unhexlify(macaroon.signature_bytes)
        macaroon.signature = sign_third_party_caveat(
            encode_key,
            caveat._verification_key_id,
            caveat._caveat_id
        )
        return macaroon


class ThirdPartyCaveatVerifierDelegate(BaseThirdPartyCaveatVerifierDelegate):

    def __init__(self, *args, **kwargs):
        super(ThirdPartyCaveatVerifierDelegate, self).__init__(*args, **kwargs)

    def verify_third_party_caveat(self,
                                  verifier,
                                  caveat,
                                  root,
                                  macaroon,
                                  discharge_macaroons,
                                  signature):
        caveat_macaroon = self._caveat_macaroon(caveat, discharge_macaroons)
        caveat_key = self._extract_caveat_key(signature, caveat)

        caveat_met = verifier.verify_discharge(
            root,
            caveat_macaroon,
            caveat_key,
            discharge_macaroons=discharge_macaroons
        )

        return caveat_met

    def update_signature(self, signature, caveat):
        return binascii.unhexlify(
            sign_third_party_caveat(
                signature,
                caveat._verification_key_id,
                caveat._caveat_id
            )
        )

    def _caveat_macaroon(self, caveat, discharge_macaroons):
        # TODO: index discharge macaroons by identifier
        caveat_macaroon = next(
            (m for m in discharge_macaroons
             if m.identifier_bytes == caveat.caveat_id_bytes), None)

        if not caveat_macaroon:
            raise MacaroonUnmetCaveatException(
                'Caveat not met. No discharge macaroon found for identifier: '
                '{}'.format(caveat.caveat_id_bytes)
            )

        return caveat_macaroon

    def _extract_caveat_key(self, signature, caveat):
        key = truncate_or_pad(signature)
        box = SecretBox(key=key)
        decrypted = box.decrypt(caveat._verification_key_id)
        return decrypted
