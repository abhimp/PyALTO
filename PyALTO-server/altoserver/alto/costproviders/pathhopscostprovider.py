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
Network path property provider returns hostnames of all nodes
in between two given IP addresses.

N.B. This is debug tool and not a cost provider per se!

N.B. This would fail STRICT RFC validation due to return value format!
"""
import logging

from altoserver import nm
from .basecostprovider import BaseCostProvider
from ..addresstypes.ipaddrparser import IPAddrParser

class PathHopsCostProvider(BaseCostProvider):
    """Implements path tracer"""

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

        for index, node in enumerate(nm.dev_to_dev_iterator(srcs[0], dsts[0])):
            path[index] = node.name

        data = {
            'source-address': self._ip_parser.from_object(srcs[0]),
            'destination-address': self._ip_parser.from_object(dsts[0]),
            'path': path
        }

        return data
