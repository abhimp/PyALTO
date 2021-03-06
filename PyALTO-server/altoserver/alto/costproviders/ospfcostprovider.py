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
Routing cost provider that is using OSPF routing distance as its cost.
"""
import ipaddress
import logging

from altoserver import nm
from .basecostprovider import BaseCostProvider
from ..addresstypes.ipaddrparser import IPAddrParser

class OSPFCostProvider(BaseCostProvider):
    """Implements OSPF routing cost provider"""

    def __init__(self):
        """Init the object and overwrite type"""
        super().__init__()
        self.cost_metric = 'ospf-routingcost'
        self.cost_mode = 'numerical'
        self.cost_type = 'ospf-routingcost'

        self._ip_parser = IPAddrParser()

    def get_cost(self, in_srcs, in_dsts):
        """Return cost based on OSPF routing cost.
        srcs and dsts
        """

        str_src = '({})'.format(';'.join(map(str, in_srcs)))
        str_dst = '({})'.format(';'.join(map(str, in_dsts)))
        logging.info('OSPF RD request: From: %s To: %s', str_src, str_dst)

        # Ensure we have something to work with
        assert any(in_srcs) and any(in_dsts)

        # Parse endpoint addrs to Python objects
        srcs = [self._ip_parser.to_object(saddr) for saddr in in_srcs]
        dsts = [self._ip_parser.to_object(daddr) for daddr in in_dsts]

        # Algorithm (for each SRC IP):
        #   1. Get Device from IP
        #   2. Go Upstream until device is router
        #   3. Get OSPF RD for each destination
        costmap = {}
        for source_ip in srcs:
            device = nm.get_device_by_ip(source_ip)

            # No such device
            if device is None:
                logging.info('Device having addr: %s not found', str(source_ip))
                continue

            # Find first hop router
            first_hop_rtr = nm.get_upstream_router(device.name)

            # Nothing found
            if first_hop_rtr is None:
                logging.info('First hop router for source ip %s not found',
                             str(source_ip))
                continue

            # Extract destination OSPF RD for each destination
            distances = {}
            for dst_addr in dsts:
                ospf_rd = self._get_ospf_rd(first_hop_rtr, dst_addr)
                if ospf_rd is not None:
                    distances[self._ip_parser.from_object(dst_addr)] = ospf_rd
                    logging.info('OSPF RD: From: %s To: %s -> %s', 
                                 str(source_ip), str(dst_addr), ospf_rd)
                else:
                    logging.info('OSPF cost from %s to %s not found',
                                 str(source_ip), str(dst_addr))

            # Save results if any
            if any(distances):
                costmap[self._ip_parser.from_object(source_ip)] = distances

        # Resulting cost-map
        return costmap

    def _get_ospf_rd(self, router_name, destination):
        """Given router name, ger OSPF RD for each destination"""

        assert (isinstance(destination, ipaddress.IPv4Address) or
                isinstance(destination, ipaddress.IPv6Address))

        router = nm.get_device_by_name(router_name)
        if router is None:
            return None

        # Check for entires in Quagga RT
        quagga_rt = router.quagga_routing_table
        if not any(quagga_rt):
            return None

        rd_min = None
        for route_line in quagga_rt:
            if route_line['protocol'] != 'O':
                continue

            # route_line is OSPF
            if destination in ipaddress.ip_network(route_line['subnet']):
                # find min RD
                if rd_min is None:
                    rd_min = route_line['RD']
                else:
                    rd_min = min([rd_min, route_line['RD']])

        return rd_min
