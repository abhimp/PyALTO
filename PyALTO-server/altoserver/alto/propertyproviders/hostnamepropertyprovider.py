"""
Implement endpoint's Hostname provider
"""
import ipaddress

from .basepropertyprovider import BasePropertyProvider
from altoserver import nm

class HostnamePropertyProvider(BasePropertyProvider):
    """Implements endpoint's Hostname provider"""

    def __init__(self):
        super().__init__()
        self.property_name = 'priv:hostname'

    def get_property(self, endpoint):
        """Return Hostname of the given endpoint"""
        
        # This class supports IP addresses only
        if (not isinstance(endpoint, ipaddress.IPv4Address) and
            not isinstance(endpoint, ipaddress.IPv6Address)):

            return None

        # Get the device
        device = nm.get_device_by_ip(endpoint)

        # Check if device found
        if device is None:
            return None

        # Return device name and meta of map this name was derived from
        return (device.name, nm.get_map_meta())
