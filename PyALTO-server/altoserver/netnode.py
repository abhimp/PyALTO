"""
Representation of network device
"""

class NetNode(object):
    """NetNode class represents a single network device"""
    # Once created, all properties should be public, but changes
    # should be strictly controlled, hence using @property.

    def __init__(self, name, dev_type):
        """Initialize the device"""
        self._upstream = None   # Upstream device (user->adslam, adslam->router, router->None)
        self._ip_addresses = [] # IP addresses assigned to device. Switch will have none
        self._name = name       # Device's name
        self._type = dev_type   # router, switch, adslam, user
        self._rt = None         # Routing table
        self._qrt = None        # Quagga routing table
        self._intf_stat = None  # Network interface stats

    @property
    def upstream(self):
        """Get name of upstream device"""
        return self._upstream

    @property
    def ip_addresses(self):
        """Get list of configured IP addresses"""
        return self._ip_addresses

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

    @routing_table.setter
    def routing_table(self, rt):
        """Update routing table"""
        assert self.type == 'router'
        self._rt = rt

    @property
    def quagga_routing_table(self):
        """Get Quagga routing table"""
        assert self._type == 'router'
        return self._qrt

    @quagga_routing_table.setter
    def quagga_routing_table(self, qrt):
        """Set new Quagga routing table"""
        assert self._type == 'router'
        self._qrt = get_qrt_iterator

    @property
    def interface_stats(self):
        """Return network interface stats"""
        return self._intf_stat

    @interface_stats.setter
    def interface_stats(self, intf_stat):
        """Set new interface stats"""
        self._intf_stat = intf_stat

    def __eq__(self, other):
        """Implement equality comparer"""
        if not isinstance(other, NetNode):
            return False

        return self.name == other.name

    def __hash__(self, **kwargs):
        """Implement hash operation, we use name"""
        return self.name.__hash__()
