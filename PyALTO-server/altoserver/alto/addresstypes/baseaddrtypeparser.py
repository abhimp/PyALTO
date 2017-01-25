"""
Base class for address type converter. See [RFC7285] p.14.4
"""

class BaseAddrTypeParser(object):
    """Implements base address type converter."""

    def __init__(self):
        """Initialize class"""
        self.identifiers = []
        self.types = []

    def to_object(self, in_addr):
        """Return object from address"""
        raise NotImplementedError

    def from_object(self, in_object):
        """Return string representation"""
        raise NotImplementedError
