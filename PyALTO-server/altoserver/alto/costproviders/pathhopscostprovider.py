"""
Network path property provider returns hostnames of all nodes
in between two given IP addresses.

N.B. This would fail STRICT RFC validation due to return value format!
"""
import ipaddress
import logging

from altoserver import nm
from .basecostprovider import BaseCostProvider
from ..addresstypes.ipaddrparser import IPAddrParser

class PathHopsCostProvider(BaseCostProvider):
    """Implements path provider"""

    def __init__(self):
        super().__init__()
        self.cost_metric = 'hops-path'
        self.cost_mode = 'numerical'
        self.cost_type = 'hops-path'

        self._ip_parser = IPAddrParser()

    def get_cost(self, in_srcs, in_dsts):
        """Return path from source to destination"""
        
        str_src = '({})'.format(';'.join(map(str, in_srcs)))
        str_dst = '({})'.format(';'.join(map(str, in_dsts)))
        logging.info('Path trace request: From: %s To: %s', str_src, str_dst)

        # Parse endpoint addrs to Python objects
        srcs = [self._ip_parser.to_object(saddr) for saddr in in_srcs]
        dsts = [self._ip_parser.to_object(daddr) for daddr in in_dsts]

        # For now it works on single IPs pair
        # TODO change later
        assert len(srcs) == 1
        assert len(dsts) == 1

        path = {}

        try:
            for index, node in enumerate(nm.dev_to_dev_iterator(srcs[0], dsts[0])):
                path[index] = node.name
        except LookupError as exc:
            logging.warning('Lookup error while tracing: {}'.format(exc))
            return {}

        data = {
            'source-address': self._ip_parser.from_object(srcs[0]),
            'destination-address': self._ip_parser.from_object(dsts[0]),
            'path': path
        }

        return data
