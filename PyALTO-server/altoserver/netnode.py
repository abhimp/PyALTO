"""
Representation of network device
"""
import collections
import ipaddress
import time

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
        return self._rt

    @property
    def quagga_routing_table(self):
        """Get Quagga routing table"""
        assert self._type == 'router'
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