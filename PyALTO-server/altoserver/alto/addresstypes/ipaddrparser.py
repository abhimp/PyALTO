"""
Implement concrete IP address parser
"""
import ipaddress
from .baseaddrtypeparser import BaseAddrTypeParser

class IPAddrParser(BaseAddrTypeParser):
    """concrete IP address parser implementation"""

    #TODO: Make class method, this object has no state

    def __init__(self):
        super().__init__()
        self.identifiers.extend(['ipv4', 'ipv6'])
        self.types.extend([ipaddress.IPv4Address, ipaddress.IPv6Address])

    def to_object(self, in_addr):
        """Convert from text representation to obj"""

        # We expect text
        assert isinstance(in_addr, str)
        assert in_addr.count(':') == 1

        # Split address and valdiate
        (addr_type, address) = in_addr.split(':')
        assert addr_type.lower() == 'ipv4' or addr_type.lower() == 'ipv6'

        # Return the IP Address object
        return ipaddress.ip_address(address)

    def from_object(self, in_object):
        """Convert from object to text representation"""

        # Ensure we are given sane parameters
        assert (isinstance(in_object, ipaddress.IPv4Address) or
                isinstance(in_object, ipaddress.IPv6Address))

        # Return strin representation
        if in_object.version == 4:
            return 'ipv4:{}'.format(str(in_object))
        else:
            return 'ipv6:{}'.format(str(in_object))
