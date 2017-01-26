"""
Representation of network device
"""

class NetNode(object):
    """NetNode class represents a single network device"""

    def __init__(self, name, dev_type):
        """Initialize the device"""

        self.name = name
        self.type = dev_type    # router, switch, adslam, user
        self.upstream = None    # Upstream device (user->adslam, adslam->router, router->None)
        self.ip_addresses = []  # IP addresses assigned to device. Switch will have none

        self._rt = None         # Routing table
        self._qrt = None        # Quagga routing table

    def update_routing_table(self, routing_table):
        """Update routing table maintained in the device"""

        # This is applicable only to router type
        assert self.type == 'router'

        self._rt = routing_table

    def update_quagga_table(self, quagga_rt):
        """Update quagga routing table"""

        # Only for routers
        assert self.type == 'router'

        self._qrt = quagga_rt

    def get_if_to(self, destination_address):
        """Get the interface to destination"""
        pass

    def get_rt_iterator(self):
        return iter(self._rt)

    def get_qrt_iterator(self):
        return iter(self._qrt)

    def __eq__(self, other):
        """Implement equality comparer"""
        if not isinstance(other, NetNode):
            return False

        return self.name == other.name

    def __hash__(self, **kwargs):
        """Implement hash operation, we use name"""
        return self.name.__hash__()
