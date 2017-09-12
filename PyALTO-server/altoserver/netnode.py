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
Representation of network device
"""
import collections
import ipaddress
import time
import logging

class NetNode(object):
    """NetNode class represents a single network device"""
    # Once created, all properties should be public, but changes
    # should be strictly controlled, hence using @property.

    def __init__(self, name, dev_type, in_ips=[], upst=None):
        """Initialize the device"""

        # Eventually this should be L2device, L3device, NFdevice (netflow switch), server, user etc.
        self._type = None       # Device type (router, switch, adslam, user)
        self._name = None       # Device name
        self._upstream = None   # Upstream device (user->adslam, adslam->router, router->None)
        self._ip_interfaces = []# IP addresses assigned to device. Switch will have none
        self._rt = None         # Routing table
        self._qrt = None        # Quagga routing table

        # Time series data
        self._adapter_stats = collections.deque([], maxlen=10)
        self._address_details = []

        self._name = name       
        self._type = dev_type
        self._ip_interfaces.extend(in_ips)
        self._upstream = upst

    @property
    def upstream(self):
        """Get name of upstream device"""
        return self._upstream

    @property
    def ip_interfaces(self):
        """Get list of configured IP addresses"""
        return self._ip_interfaces

    @property
    def name(self):
        """Get device name"""
        return self._name

    @property
    def type(self):
        """Get device type"""
        return self._type

    @property
    def routing_table(self):
        """Get routing table"""
        assert self._type == 'router'
        if self._rt is None:
            return []
        else:
            return self._rt

    @property
    def quagga_routing_table(self):
        """Get Quagga routing table"""
        assert self._type == 'router'
        if self._qrt is None:
            return []
        else:
            return self._qrt

    @property
    def interface_stats(self):
        """Return latest observed adapter stats"""
        return self._adapter_stats[-1]

    def update_interface_addresses(self, addr_data):
        """Called with new interface data"""

        # Update assigned IP addresses
        self._ip_interfaces.clear()

        for intf_addr in addr_data:
            ip_intf = ipaddress.ip_interface(intf_addr['address'])
            self._ip_interfaces.append(ip_intf)
            logging.info('%s : Added interface: %s', self, str(ip_intf))

        # Save detailed data for (any) later use
        self._address_details.clear()
        self._address_details.extend(addr_data)

    def update_adapter_stats(self, adapter_stats):
        """Append latest counters"""

        # Add stats with timestamp
        self._adapter_stats.append((time.time(), adapter_stats))

    def update_routing_table(self, rt_data):
        """Update Routing table data"""

        assert self.type == 'router'
        self._rt = rt_data

    def update_quagga_routing_table(self, qrt_data):
        """Update Quagga RT"""

        assert self.type == 'router'
        self._qrt = qrt_data

    def get_adapter_tx_load(self, adapter_name: str) -> int:
        """Get TX load in bps of given adapter"""
        
        # Do we have any measurements?
        num_samples = len(self._adapter_stats)
        if num_samples < 2:
            return None

        (time_1, stats_1) = self._adapter_stats[-1]
        (time_2, stats_2) = self._adapter_stats[-2]
        
        adapter_stat_1 = None
        adapter_stat_2 = None

        for adapter_stat in stats_1:
            if adapter_stat['name'] == adapter_name:
                adapter_stat_1 = adapter_stat['stats']

        for adapter_stat in stats_2:
            if adapter_stat['name'] == adapter_name:
                adapter_stat_2 = adapter_stat['stats']

        if adapter_stat_1 is None or adapter_stat_2 is None:
            logging.warning('Did not find adapter %s in node %s', adapter_name, self.name)
            return None

        # x_1 > x_2
        delta_t = time_1 - time_2
        delta_d = (adapter_stat_1['tx_bytes'] - adapter_stat_2['tx_bytes']) * 8

        assert delta_t != 0

        return delta_d/delta_t

    def get_adapter_rx_load(self, adapter: str) -> int:
        """Get RX load in bps of given adapter"""
        
        # Do we have any measurements?
        num_samples = len(self._adapter_stats)
        if num_samples < 2:
            return None

        (time_1, stats_1) = self._adapter_stats[-1]
        (time_2, stats_2) = self._adapter_stats[-2]
        
        adapter_stat_1 = None
        adapter_stat_2 = None

        for adapter_stat in stats_1:
            if adapter_stat['name'] == adapter:
                adapter_stat_1 = adapter_stat['stats']

        for adapter_stat in stats_2:
            if adapter_stat['name'] == adapter:
                adapter_stat_2 = adapter_stat['stats']

        if adapter_stat_1 is None or adapter_stat_2 is None:
            logging.warning('Did not find adapter %s in node %s', adapter_name, self.name)
            return None

        # x_1 > x_2
        delta_t = time_1 - time_2
        delta_d = (adapter_stat_1['rx_bytes'] - adapter_stat_2['rx_bytes']) * 8

        assert delta_t != 0

        return int(delta_d/delta_t)

    def rt_longest_prefix_match(self, destination_ip, return_default=False):
        """Perform LPM based on destination and return (intf, gw) 
        or None. use_default allow default route to be returned
        (if present)."""

        assert self._type == 'router'
        if self._rt is None:
            return None

        # Match route lines
        # TODO: change from str interpolation to ctor with (str,str) in Py3.6
        rt_lines = [line for line in self._rt 
                    if destination_ip in ipaddress.ip_network('{}/{}'.format(
                        line['destination'], line['mask']))]
       
        if any(rt_lines):
            lpm_line = max(rt_lines, key=lambda x: 
                           ipaddress
                            .ip_network('{}/{}'.format(
                                x['destination'], x['mask']))
                            .prefixlen)

            return (lpm_line['ifname'], lpm_line['gateway'])
        elif not return_default:
            # Do not return default 
            return None
        else:
            # Try to return default
            def_route = [rt_line for rt_line in self._rt if 'G' in rt_line['flags']]
            if any(def_route):
                return def_route[0]
            else:
                return None

    def __eq__(self, other):
        """Implement equality comparer"""
        
        # If accessing as string
        if isinstance(other, str):
            return self.name == other

        # Else do normal checking
        if not isinstance(other, NetNode):
            return False

        return self.name == other.name

    def __hash__(self, **kwargs):
        """Implement hash operation, we use name"""
        return self.name.__hash__()

    def __str__(self):
        return 'Node: {} Type: {}'.format(self.name, self.type)

    def __repr__(self):
        return self.__str__()
