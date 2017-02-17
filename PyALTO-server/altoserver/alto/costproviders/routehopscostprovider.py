"""
Implements ALTO cost provider using number of L3 (router) hops
between source and destination as the routing cost metric. This
costmetric is the same as the one used by RIP family of routing
protocols with the only exception that it can be over 15. In RIP
everything over 15 routing hops is considered unreachable.
"""

import ipaddress
import logging

from altoserver import nm
from .basecostprovider import BaseCostProvider
from ..addresstypes.ipaddrparser import IPAddrParser

class RouteHopsCostProvider(BaseCostProvider):
    """Class implementing Route Hop cost provider"""

    def __init__(self):
        """Initialize the cost provider"""
        super().__init__()
        self.cost_metric = 'hops-routingcost'
        self.cost_mode = 'numerical'
        self.cost_type = 'hops-routingcost'

        self._ip_parser = IPAddrParser()

    def get_cost(self, in_srcs, in_dsts):
        """Return cost map based on number of
        routing hops between srcs and dsts"""

        # Print logging details
        str_src = '({})'.format(';'.join(map(str, in_srcs)))
        str_dst = '({})'.format(';'.join(map(str, in_dsts)))
        logging.info('RouteHops request: From: %s To: %s', str_src, str_dst)

        # Ensure we have something to work with
        assert any(in_srcs) and any(in_dsts)

        # Parse endpoint addrs to Python objects
        srcs = [self._ip_parser.to_object(saddr) for saddr in in_srcs]
        dsts = [self._ip_parser.to_object(daddr) for daddr in in_dsts]

        # N.B. This cost CAN be 0 if source and destination is connected
        # directly or over the switch type device. If the SRC==DST, this
        # will be set to 0.
        costmap = {}
        for source_ip in srcs:

            # Get the source device
            device = nm.get_device_by_ip(source_ip)
            if device is None:
                logging.info('Device having addr: %s not found', str(source_ip))
                continue

            # One the device if found, trace to all destinations
            distances = {}
            for destination_ip in dsts:
                cost = self._trace_l3_hops(device, source_ip, destination_ip)
                if cost is None:
                    logging.info('No cost from %s to %s',
                                 str(source_ip), str(destination_ip))
                    continue
                else:
                    logging.info('Cost from %s to %s is %s',
                                 str(source_ip), str(destination_ip), cost)
                    distances[self._ip_parser.from_object(destination_ip)] = cost

            # Save results if any
            if any(distances):
                costmap[self._ip_parser.from_object(source_ip)] = distances

        #Return costmap
        return costmap

    def _trace_l3_hops(self, src_device, source, destination):
        """Trace the path from source to destination
        returning number of network hops"""

        # Handle some of the corner cases
        if source == destination:
            return 0

        # Get interface having source ip
        src_intf = None
        for intf in src_device.ip_interfaces:
            if intf.ip == source:
                src_intf = intf

        # Are devices connected to the same broadcast domain
        if destination in src_intf.network:
            return 0

        # At this point the destination is at least 1 hop away
        # If this is router do nothing, else - get FHR
        cur_rtr = None
        if src_device.type == 'router':
            cur_rtr = src_device
        if src_device.type != 'router':
            fhr_name = self._get_upstream_router(src_device.name)
            if fhr_name is None:
                logging.warning('Could not get FHR for dev %s', src_device.name)
                return None
            cur_rtr = nm.get_device_by_name(fhr_name)

        # Loop through network until target rtr is found
        routing_distance = 0
        ttl = 128   # Adjust this for your network size
        while True:
            # Prevent infinite looping
            if ttl == 0:
                logging.warning('TTL expired while tracing from %s to %s',
                                str(source), str(destination))
                return None

            # Get the line-of-interest from the routing table
            rtable = cur_rtr.routing_table
            if not any(rtable):
                logging.warning('Routing table empty in %s', cur_rtr.name)
                return None

            route_line = None
            for line in rtable:
                network = ipaddress.ip_network('{}/{}'.format(
                    line['destination'], line['mask']))
                if destination in network:
                    route_line = line
                    break

            if route_line is None:
                logging.warning('Did not find route to %s in rtr %s',
                                destination, cur_rtr.name)
                return None

            # We have route line, check what to do next
            if 'G' not in route_line['flags']:
                # Do not use gateway - destination conencted directly!
                break
            else:
                # Get the GW router
                cur_rtr = nm.get_device_by_ip(route_line['gateway'])
                if cur_rtr is None:
                    logging.warning('Did not find device with IP: %s', route_line['gateway'])
                    return None
                routing_distance += 1
                ttl -= 1
                continue

        # Adjust the final value
        if src_device.type != 'router':
            routing_distance += 1

        return routing_distance


    def _get_upstream_router(self, device_name):
        """Given the device name find first hop router"""

        device = nm.get_device_by_name(device_name)

        if device is None:
            return None
        elif device.type == 'router':
            return device.name
        else:
            return self._get_upstream_router(device.upstream)
