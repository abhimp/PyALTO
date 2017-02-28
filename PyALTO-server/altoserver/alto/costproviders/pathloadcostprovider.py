"""
Routing cost provider that is using residual path capacity as cost metric.
To calculate residual path load, obtain path from source to destinatio.
If path exists, it will contain one ot more segments (links between devices).
For each link, calculate the residual bandwidth (link capacity - link load).
Cost metric is the minimal valuo of all segments capacity. It shows the highest
available bandwidth along the path from source to destination.
"""
import ipaddress
import logging

from altoserver import nm
from .basecostprovider import BaseCostProvider
from ..addresstypes.ipaddrparser import IPAddrParser

class PathLoadCostProvider(object):
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

    def __init__(self):
        """Init the cost provider"""
        super().__init__()
        self.cost_metric = 'ospf-routingcost'
        self.cost_mode = 'numerical'
        self.cost_type = 'residual-pathbandwidth'

        self._ip_parser = IPAddrParser()

    def get_cost(self, in_src, in_dst):
        """Return cost based on the residual bandwidth"""

        # Print logging details
        str_src = '({})'.format(';'.join(map(str, in_srcs)))
        str_dst = '({})'.format(';'.join(map(str, in_dsts)))
        logging.info('ResidualPathBW request: From: %s To: %s', str_src, str_dst)

        # Ensure we have something to work with
        assert any(in_srcs) and any(in_dsts)

        # Parse endpoint addrs to Python objects
        srcs = [self._ip_parser.to_object(saddr) for saddr in in_srcs]
        dsts = [self._ip_parser.to_object(daddr) for daddr in in_dsts]
        
        pass

    def _trace_path(self, src_ip, dst_ip):
        """Trace path from source to destination nodes"""

        # Get the source device
        src_dev = nm.get_device_by_ip(src_ip)
        if src_dev is None:
            logging.info('Failed to find device having IP: %s', str(src_ip))
            return None

        # Ensure source != dest
        for ip_int in src_dev.ip_interfaces:
            if ip_int.ip == dst_ip:
                logging.info('%s and %s belong to the same device', str(src_ip), str(dst_ip))
                return -1

        # Start tracing
        cur_device = src_dev # Tracing pointer
        residual_bws = []

        # Trace out way to the first hop router
        while True:
            if cur_device.type == 'user' or cur_device.type == 'adslam':
                rbw = self._get_upstream_residualbw_backward(cur_device)
                cur_device = nm.get_device_by_name(cur_device.upstream)
                residual_bws.append(rbw)
            elif cur_device.type == 'router':
                break
            else:
                logging.warning('Unexpected device type: %s', cur_device.type)
                return -1

        # Trace between the routers
        ttl = 128 # Prevent infinite tracing
        while True:
            if ttl == 0:
                logging.warning('TTL expired while tracing from %s to %s',
                                str(src_ip), src(dst_ip))
                return -1

            # Get the routing table
            rtable = cur_device.routing_table
            if not any(rtable):
                logging.warning('Routing table empty in %s', cur_device.name)
                return -1

            # Extract the line with our destination
            # TODO: Longest-prefix match
            route_line = None
            for line in rtable:
                network = ipaddress.ip_network('{}/{}'.format(
                    line['destination'], line['mask']))
                if dst_ip in network:
                    route_line = line
                    break

            if route_line is None:
                logging.warning('Did not find route to %s in router %s',
                                str(dst_ip), cur_device.name)
                return -1

            # Are we going to next router or destination device is connected
            if 'G' not in route_line['flags']:
                break
            else:
                next_dev = nm.get_device_by_ip(ipaddress.ip_address(route_line['gateway']))
                if next_dev is None:
                    logging.warning('Did not find device with IP: %s', route_line['gateway'])
                    return -1
                rbw = self._get_residualbw_from_dev_int_to_dev(
                    cur_device, route_line['ifname'], next_dev)
                residual_bws.append(rbw)
                cur_device = next_dev
                ttl -= 1
                continue

        # Now we are at the last router (cur_device)
        dev = cur_device.rt_longest_prefix_match(dst_ip)
        if dev is None:
            logging.warning('Last router %s has no connection to %s',
                            cur_device.name, dst_ip)
            return -1

        # Get remote device and interface
        (cur_local, cur_gw) = dev
        rem = nm.core_data.get_remote_peer(cur_device.name, cur_local)
        if rem is None:
            logging.warning('Failed to find device connected to %s %s',
                            cur_device.name, cur_local)
            return -1

        # Get remote device
        (rem_hostname, rem_loc) = rem
        rem_dev = nm.get_device_by_name(rem_hostname)
        if rem_dev is None:
            logging.warning('Failed to retrieve device %s', rem_hostname)
            return -1

        # This is either user, adslam or router.
        if rem_dev.type == 'router' or rem_dev.type == 'user':
            for local_intf in rem_dev.ip_interfaces:
                if local_intf.ip == dst_ip:
                    rbw = self._get_residualbw_from_dev_int_to_dev(cur_device, cur_local, rem_dev)
                    residual_bws.append(rbw)
                    return residual_bws
                else:
                    logging.warning('Last device %s has no IP: %s', rem_dev.name, str(dst_ip))
                    return -1
        elif rem_dev.type == 'adslam':
            # Iterate though out edges and find device having dst IP
            for (a_node, b_node, params) in nm.get_out_edges(rem_dev):
                for local_intf in b_node.ip_interfaces:
                    if local_intf.ip == dst_ip:
                        # TODO
                        pass
        else:
            logging.warning('Device %s has unknown type %s', rem_dev.name, rem_dev.type)
            return -1
                

    def _get_residualbw_from_dev_int_to_dev(self, src_dev, src_intf, dst_dev):
        """Get residual BW between source and destination when leaving via src_intf"""
        link_cap = PathLoadCostProvider.get_link_capacity(src_dev, dst_dev)
        load = src_dev.get_tx_load(src_intf)

        # Calculate residual BW
        if link_cap is None:
            logging.info('Unable to get link capacity from %s to %s',
                         src_dev.name, dst_dev.name)
            return -1

        if load is None:
            return link_cap
        else:
            return max([link_cap-load, 0])

    def _get_upstream_residualbw_backward(self, source_dev) -> int:
        """Get residual BW from source device to upstream by
        using received data load on upstream device"""

        # Get primary data
        upstream_load = self._get_uptream_rx_load(cur_device)
        upstream_dev = nm.get_device_by_name(cur_device.upstream)
        link_cap = PathLoadCostProvider.get_link_capacity(
            cur_device, upstream_dev)

        # Calculate residual BW
        if link_cap is None:
            logging.info('Unable to get link capacity from %s to %s',
                         cur_device.name, cur_device.upstream)
            return -1

        if upstream_load is None:
            return link_cap
        else:
            return max([link_cap-upstream_load,0])

    def _get_uptream_rx_load(self, node):
        """Get RX data load on link from node to upstream"""
        
        upstream_name = node.upstream
        upstream_dev = nm.get_device_by_name(upstream_name)
        
        if upstream_dev is None:
            logging.warning('Node: %s does not have upstream', node.name)
            return None

        # Get adapter details
        connection = nm.core_data.get_adapter_names(node.name, upstream_name)
        if connection is None:
            logging.warning('No connection between %s and %s', node.name, upstream_name)

        # Parse data
        ((node_global, node_local), (upst_global, upst_local)) = connection

        # Get RX load on upstream from node
        return upstream_dev.get_adapter_rx_load(upst_local)
