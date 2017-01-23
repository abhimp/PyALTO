"""
Representation of network device
"""

class NetNode(object):
    """NetNode class represents a single network device"""

    def __init__(self, name, dev_type):
        """Initialize the device"""

        self.name = name
        self.type = dev_type    # router, switch, adslam

        self._rt = None

    def update_routing_table(self, routing_table):
        """Update routing table maintained in the device"""

        # This is applicable only to router type
        assert self.type == 'router'

        self._rt = routing_table

    def get_if_to(self, destination_address):
        """Get the interface to destination"""
        pass

    def __eq__(self, other):
        """Implement equality comparer"""
        if not isinstance(other, NetNode):
            return False

        return self.name == other.name

    def __hash__(self, **kwargs):
        """Implement hash operation, we use name"""
        return self.name.__hash__()
