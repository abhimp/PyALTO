"""
PyALTO, a Python3 implementation of Application Layer Traffic Optimization protocol
Copyright (C) 2016,2017  J. Poderys, Technical University of Denmark

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

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
