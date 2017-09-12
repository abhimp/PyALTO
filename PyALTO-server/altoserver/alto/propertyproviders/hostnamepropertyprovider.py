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
Implement endpoint's Hostname provider
"""
import ipaddress
import logging

from .basepropertyprovider import BasePropertyProvider
from altoserver import nm

class HostnamePropertyProvider(BasePropertyProvider):
    """Implements endpoint's Hostname provider"""

    def __init__(self):
        super().__init__()
        self.property_name = 'priv:hostname'

    def get_property(self, endpoint):
        """Return Hostname of the given endpoint"""
        
        logging.info('Hostname request for: %s', str(endpoint))

        # This class supports IP addresses only
        if (not isinstance(endpoint, ipaddress.IPv4Address) and
            not isinstance(endpoint, ipaddress.IPv6Address)):

            return None

        # Get the device
        device = nm.get_device_by_ip(endpoint)

        # Check if device found
        if device is None:
            logging.info('Device with IP %s not found', endpoint)
            return None

        # Return device name and meta of map this name was derived from
        return (device.name, nm.get_map_meta())
