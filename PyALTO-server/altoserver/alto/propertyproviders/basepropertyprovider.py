class BasePropertyProvider(object):
    """Implements base class for all property providers"""

    def __init__(self):
        """Initialize common properties"""
        self.property_name = ''

    def get_property(self, endpoint):
        """Return value of the property"""
        raise NotImplementedError
