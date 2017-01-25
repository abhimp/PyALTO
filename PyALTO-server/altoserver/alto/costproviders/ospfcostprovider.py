"""
Routing cost provider that is using OSPF routing distance as its cost.
"""
from altoserver.alto.costproviders.basecostprovider import BaseCostProvider
from altoserver import nm

class OSPFCostProvider(BaseCostProvider):
    """Implements OSPF routing cost provider"""

    def __init__(self):
        """Init the object and overwrite type"""
        super().__init__()
        self.cost_metric = 'routingcost'
        self.cost_mode = 'numerical'

    def get_cost(self, srcs, dsts):
        """Return cost based on OSPF routing cost.
        srcs and dsts is [ipaddress]
        """

        # Ensure we have something to work with
        assert any(srcs) and any(dsts)

        # Get the PID of source IP
        pass
