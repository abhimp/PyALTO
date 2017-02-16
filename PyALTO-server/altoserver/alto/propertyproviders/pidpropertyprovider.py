"""
Implement endpoint's PID provider
"""
import ipaddress
import logging

from .basepropertyprovider import BasePropertyProvider
from altoserver import nm

class PIDPropertyProvider(BasePropertyProvider):
    """Implements endpoint's PID provider"""

    def __init__(self):
        super().__init__()
        self.property_name = 'network-map.pid'

    def get_property(self, endpoint):
        """Return PID and dependant VTAGs of given endpoint"""

        logging.info('PID lookup for endpoint: %s', str(endpoint))

        # This class supports IP addresses only
        if (not isinstance(endpoint, ipaddress.IPv4Address) and
            not isinstance(endpoint, ipaddress.IPv6Address)):

            return None

        # Try to find the PID
        endpoint_pid = nm.get_pid_from_ip(endpoint)

        # Did we find anything?
        if endpoint_pid is None:
            logging.info('PID lookup failed. No device with endpoint: %s', str(endpoint))
            return None

        # Return with dependant information
        return (endpoint_pid, nm.get_map_meta())
