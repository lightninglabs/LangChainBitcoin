from abc import ABCMeta, abstractmethod


class BaseSerializer(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def serialize(self, macaroon):
        pass

    @abstractmethod
    def deserialize(self, serialized):
        pass
