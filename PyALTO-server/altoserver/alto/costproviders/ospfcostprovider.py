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
        self.cost_metric = 'routingcost'
        self.cost_mode = 'numerical'
        self.cost_type = 'ospf-routingcost'

        self._ip_parser = IPAddrParser()

    def get_cost(self, srcs, dsts):
        """Return cost based on OSPF routing cost.
        srcs and dsts is [ipaddress]
        """

        str_src = '({})'.format(';'.join(map(str, srcs)))
        str_dst = '({})'.format(';'.join(map(str, dsts)))
        logging.info('OSPF RD request: From: %s To: %s', str_src, str_dst)

        # Ensure we have something to work with
        assert any(srcs) and any(dsts)

        # Algorithm (for each SRC IP):
        #   1. Get Device from IP
        #   2. Go Upstream until device is router
        #   3. Get OSPF RD for each destination
        costmap = {}
        for source_ip in srcs:
            device = nm.get_device_by_ip(source_ip)

            # No such device
            if device is None:
                continue

            # Find first hop router
            first_hop_rtr = self._get_upstream_router(device.name)

            # Nothing found
            if first_hop_rtr is None:
                continue

            # Extract destination OSPF RD for each destination
            distances = {}
            for dst_addr in dsts:
                ospf_rd = self._get_ospf_rd(first_hop_rtr, dst_addr)
                if ospf_rd is not None:
                    distances[self._ip_parser.from_object(dst_addr)] = ospf_rd
                    logging.info('OSPF RD: From: %s To: %s -> %s', 
                                 str(source_ip), str(dst_addr), ospf_rd)

            # Save results if any
            if any(distances):
                costmap[self._ip_parser.from_object(source_ip)] = distances

        # Resulting cost-map
        return costmap

    def _get_upstream_router(self, device_name):
        """Given the device name find first hop router"""

        device = nm.get_device_by_name(device_name)

        if device is None:
            return None
        elif device.type == 'router':
            return device.name
        else:
            self._get_upstream_router(device.upstream)

    def _get_ospf_rd(self, router_name, destination):
        """Given router name, ger OSPF RD for each destination"""

        assert (isinstance(destination, ipaddress.IPv4Address) or
                isinstance(destination, ipaddress.IPv6Address))

        router = nm.get_device_by_name(router_name)
        if router is None:
            return None

        rd_min = None
        for route_line in router.quagga_routing_table():
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
