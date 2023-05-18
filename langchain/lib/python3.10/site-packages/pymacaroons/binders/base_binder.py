from abc import ABCMeta, abstractmethod


class BaseBinder(object):
    __metaclass__ = ABCMeta

    def __init__(self, root):
        self.root = root

    def bind(self, discharge):
        protected = discharge.copy()
        protected.signature = self.bind_signature(discharge.signature_bytes)
        return protected

    @abstractmethod
    def bind_signature(self, signature):
        pass
