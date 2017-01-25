"""
Base class that all cost estimators should extend
"""

class BaseCostProvider(object):
    """Abstract class"""

    def __init__(self, **kwargs):
        """Set properties"""
        self.cost_mode = None
        self.cost_metric = None
        self.cost_type = None

    def get_cost(self, srcs, dsts):
        """Extending class should implement this"""
        raise NotImplementedError()
