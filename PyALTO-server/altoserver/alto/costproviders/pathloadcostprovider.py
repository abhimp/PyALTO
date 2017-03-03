"""
Routing cost provider that is using residual path capacity as cost metric.
To calculate residual path load, obtain path from source to destinatio.
If path exists, it will contain one ot more segments (links between devices).
For each link, calculate the residual bandwidth (link capacity - link load).
Cost metric is the minimal valuo of all segments capacity. It shows the highest
available bandwidth along the path from source to destination.
"""
import logging

from altoserver import nm
from .basecostprovider import BaseCostProvider
from ..addresstypes.ipaddrparser import IPAddrParser

class PathLoadCostProvider(BaseCostProvider):
    """Implements cost estimator using residual path bandwidth"""

    @staticmethod
    def get_link_capacity(from_node, to_node):
        """Get link capacity between given nodes"""
        for (a_node, b_node, params) in nm.get_out_edges(from_node):

            # Sanity check
            assert a_node == from_node

            # Are we connected to the required node
            if b_node == to_node:
                # Get capacity or None
                return params.get('capacity')

        # Not found
        return None

    @staticmethod
    def get_residual_bw_for_path(path):
        """Given {Step->Node} path, get residual bw"""

        residual_bws = []
        idx_node_a = 0
        idx_node_b = 1
        pairs_left = len(path) - 1
        debug_str = ''

        while pairs_left:
            node_a = path[idx_node_a]
            node_b = path[idx_node_b]

            # Get link's capacity
            cap_a_to_b = PathLoadCostProvider.get_link_capacity(
                node_a, node_b)
            if cap_a_to_b is None:
                logging.warning('No known capacity from %s to %s',
                                node_a, node_b)
                return None

            # We do not know user-to-user links load, so use link's capacity
            if node_a.type == 'user' and node_b.type == 'user':
                residual_bws.append(cap_a_to_b)

                idx_node_a += 1
                idx_node_b += 1
                pairs_left -= 1

                continue

            # Get adapter details
            adapters = nm.core_data.get_adapter_names(node_a.name, node_b.name)
            if adapters is None:
                logging.warning('Unable to get adapters conencting %s to %s',
                                node_a, node_b)
                return None

            ((node_a_global, node_a_local), (node_b_global, node_b_local)) = adapters

            load = None
            rbw = None

            # Get RX BW on node_b of TX BW on node_a
            if node_b.type == 'user':
                # Get upload from dev A
                load = node_a.get_adapter_tx_load(node_a_local)
                if load is None:
                    rbw = cap_a_to_b
                else:
                    load = int(load)
                    rbw = max([0, cap_a_to_b - load])
            else:
                # Get download from dev B
                load = node_b.get_adapter_rx_load(node_b_local)
                if load is None:
                    rbw = cap_a_to_b
                else:
                    load = int(load)
                    rbw = max([0, cap_a_to_b - load])

            residual_bws.append(rbw)
            debug_str = ';'.join([
                debug_str, 
                '{} -> {} Cap/Load/RBW {}/{}/{}'
                .format(node_a.name, node_b.name, cap_a_to_b, load, rbw)
            ])

            # Continue on the path
            idx_node_a += 1
            idx_node_b += 1
            pairs_left -= 1

        logging.info(debug_str)
        return min(residual_bws)

    def __init__(self):
        """Init the cost provider"""
        super().__init__()
        self.cost_metric = 'residual-pathbandwidth'
        self.cost_mode = 'numerical'
        self.cost_type = 'residual-pathbandwidth'

        self._ip_parser = IPAddrParser()

    def get_cost(self, in_srcs, in_dsts):
        """Return cost based on the residual bandwidth"""

        str_src = '({})'.format(';'.join(map(str, in_srcs)))
        str_dst = '({})'.format(';'.join(map(str, in_dsts)))
        logging.info('Path trace request: From: %s To: %s', str_src, str_dst)

        # Parse endpoint addrs to Python objects
        srcs = [self._ip_parser.to_object(saddr) for saddr in in_srcs]
        dsts = [self._ip_parser.to_object(daddr) for daddr in in_dsts]

        costmap = {}

        # Loop over sources and destinations
        for src in srcs:
            this_src = {}

            for dst in dsts:

                # Get path
                this_path = {}
                for index, node in enumerate(nm.dev_to_dev_iterator(src, dst)):
                    this_path[index] = node

                # Get residual BW
                rbw = PathLoadCostProvider.get_residual_bw_for_path(this_path)
                if rbw is None:
                    continue

                # If rbw is known - save it
                this_src[self._ip_parser.from_object(dst)] = rbw

            # If we found any RBW's for this source - save it
            if any(this_src):
                costmap[self._ip_parser.from_object(src)] = this_src

        return costmap
