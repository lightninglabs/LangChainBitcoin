from abc import ABCMeta, abstractmethod


class BaseFirstPartyCaveatDelegate(object):
    __metaclass__ = ABCMeta

    def __init__(self, *args, **kwargs):
        super(BaseFirstPartyCaveatDelegate, self).__init__(*args, **kwargs)

    @abstractmethod
    def add_first_party_caveat(self, macaroon, predicate, **kwargs):
        pass


class BaseFirstPartyCaveatVerifierDelegate(object):
    __metaclass__ = ABCMeta

    def __init__(self, *args, **kwargs):
        super(BaseFirstPartyCaveatVerifierDelegate, self).__init__(
            *args, **kwargs
        )

    @abstractmethod
    def verify_first_party_caveat(self, verifier, caveat, signature):
        pass

    @abstractmethod
    def update_signature(self, signature, caveat):
        pass
