"""
Classes related to network topology capture and representation.
"""
import ipaddress
import hashlib
import logging

from networkx import nx
from altoserver.netnode import NetNode
from altoserver.corenetdata import CoreNetData

class NetworkMap(object):
    """Holder of network topology"""

    cap = {}

    def __init__(self):
        """Initialize the network topology"""

        # Topology as MultiDiGraph (MultiDi - Since each link is two unidirectional edges)
        self._topo = nx.MultiDiGraph()
        self._net_pids = {}             # Pin_Name -> Pid object
        self._topo_version = 0          # Each topology change should change the version number
        
        self.core_data = CoreNetData()
        self.core_data.load_data(r'/tmp/netdata.json')
        #self.core_data.load_data(r'C:\PyPPSPP\netdata.json')

    def get_out_edges(self, node):
        """Get node's out edges list"""
        return self._topo.out_edges([node], False, True)

    def get_in_edges(self, node):
        """Get node's in edges list"""
        return self._topo.in_edges([node], False, True)
        
    def add_pid_to_topology(self, name, ip_prefixes):
        """Add a PID to topology. ip_prefixes -> [IPv4/v6Network]"""

        try:
            new_pid = AltoPID(name, ip_prefixes)
        except:
            return False

        # This overwrites old value
        self._net_pids[new_pid.name] = new_pid

    def init_small_topo(self):
        """Create a simple small topology"""

        self.cap = {
            'homelink': 10000000,
            'adslamlink': 30000000,
            'bnglink': 100000000,
            'servlink': 100000000
        }

        core = NetNode('core-0', 'router')
        self._topo.add_node(core)
        self.add_pid_to_topology('core-dc', [
            ipaddress.ip_network('192.168.240.0/24'),
            ipaddress.ip_network('192.168.245.0/24')
        ])

        src = NetNode(
            'src-0',
            'user',
            [ipaddress.ip_interface('192.168.245.2/30')],
            core.name
        )
        self._topo.add_node(src)
        

        global_adslam_index = 0
        homes_per_adslam = 6

        for brasid in range(3):
            bras_name = 'bras-{}'.format(brasid)
            bras = NetNode(bras_name, 'router')
            self._topo.add_node(bras)

            for adslamid in range(2):
                # Build IP range for ADSLAM
                this_adslam_id = global_adslam_index
                global_adslam_index += 1
                adslam_prefix = '192.168.{}.0/24'.format(this_adslam_id)
                adslam_name = 'adslam-{}'.format(this_adslam_id)
                adslam_net = ipaddress.ip_network(adslam_prefix)

                # Add ADSLAM Object
                adslam = NetNode(adslam_name, 'adslam', [], bras_name)
                self._topo.add_node(adslam)
                self._topo.add_edge(adslam, bras, capacity=self.cap['adslamlink'])
                self._topo.add_edge(bras, adslam, capacity=self.cap['adslamlink'])

                # Add conencted homes
                for home_id in range(0, homes_per_adslam+1):
                    home_name = 'home-{}-{}'.format(this_adslam_id, home_id)
                    home = NetNode(
                        home_name,
                        'user',
                        [
                            ipaddress.ip_interface(
                                '{}/{}'.format(
                                    str(adslam_net[home_id+2]),
                                    '32'
                                )
                            )
                        ],
                        adslam_name
                    )
                    self._topo.add_node(home)
                    self._topo.add_edge(home, adslam, capacity=self.cap['homelink'])
                    self._topo.add_edge(adslam, home, capacity=self.cap['homelink'])

                # Add pid representing ADSLAM
                self.add_pid_to_topology(adslam_name, [adslam_net])

        # connect BRAS/CORE
        self._topo.add_edge('bras-0', 'bras-1', capacity=self.cap['bnglink'])
        self._topo.add_edge('bras-1', 'bras-0', capacity=self.cap['bnglink'])

        self._topo.add_edge('bras-1', 'bras-2', capacity=self.cap['bnglink'])
        self._topo.add_edge('bras-2', 'bras-1', capacity=self.cap['bnglink'])

        self._topo.add_edge('bras-0', 'bras-2', capacity=self.cap['bnglink'])
        self._topo.add_edge('bras-2', 'bras-0', capacity=self.cap['bnglink'])

        self._topo.add_edge('bras-0', 'core-0', capacity=self.cap['servlink'])
        self._topo.add_edge('core-0', 'bras-0', capacity=self.cap['servlink'])

        self._topo.add_edge('bras-2', 'core-0', capacity=self.cap['servlink'])
        self._topo.add_edge('core-0', 'bras-2', capacity=self.cap['servlink'])

        self._topo.add_edge('core-0', 'src-0', capacity=self.cap['servlink'])
        self._topo.add_edge('src-0', 'core-0', capacity=self.cap['servlink'])

    def init_simple_topo(self):
        """Create a simple topology for testing"""

        self.cap = {
            'homelink': 10000000,
            'adslamlink': 30000000,
            'bnglink': 100000000,
            'servlink': 100000000
        }

        # For use by dev machine
        core = NetNode('core-0', 'router')
        self._topo.add_node(core)

        src = NetNode(
            'src-0',
            'user',
            [ipaddress.ip_interface('192.168.245.2/30')],
            core.name
        )
        self._topo.add_node(src)

        # ADSLAM user's IPs are:
        # 192.168.<ADSLAM_ID>.<USER_ID+2>/24 (USER_ID=1 reserved for router)
        num_bras = 8
        adslams_per_bras = 2
        homes_per_adslam = 6

        global_adslam_index = 0     # Counter for ADSLAM numbers
        
        # Build BRAS->ADSLAM->HOME network
        for bras_id in range(0, num_bras):
            # Build BRAS as connected infrastructure
            bras_name = 'bras-{}'.format(bras_id)
            bras = NetNode(bras_name, 'router')
            self._topo.add_node(bras)

            for adslam_id in range(0, adslams_per_bras+1):
                # Build IP range for ADSLAM
                this_adslam_id = global_adslam_index
                global_adslam_index += 1
                adslam_prefix = '192.168.{}.0/24'.format(this_adslam_id)
                adslam_name = 'adslam-{}'.format(this_adslam_id)
                adslam_net = ipaddress.ip_network(adslam_prefix)

                # Add ADSLAM Object
                adslam = NetNode(adslam_name, 'adslam', [], bras_name)
                self._topo.add_node(adslam)
                self._topo.add_edge(adslam, bras, capacity=self.cap['adslamlink'])
                self._topo.add_edge(bras, adslam, capacity=self.cap['adslamlink'])

                # Add conencted homes
                for home_id in range(0, homes_per_adslam+1):
                    home_name = 'home-{}-{}'.format(this_adslam_id, home_id)
                    home = NetNode(
                        home_name,
                        'user',
                        [
                            ipaddress.ip_interface(
                                '{}/{}'.format(
                                    str(adslam_net[home_id+2]),
                                    '32'
                                )
                            )
                        ],
                        adslam_name
                    )
                    self._topo.add_node(home)
                    self._topo.add_edge(home, adslam, capacity=self.cap['homelink'])
                    self._topo.add_edge(adslam, home, capacity=self.cap['homelink'])

                # Add pid representing ADSLAM
                self.add_pid_to_topology(adslam_name, [adslam_net])

        # Interconnect BRASes
        self._topo.add_edge('bras-0', 'bras-1', capacity=self.cap['bnglink'])
        self._topo.add_edge('bras-1', 'bras-0', capacity=self.cap['bnglink'])

        self._topo.add_edge('bras-1', 'bras-2', capacity=self.cap['bnglink'])
        self._topo.add_edge('bras-2', 'bras-1', capacity=self.cap['bnglink'])

        self._topo.add_edge('bras-2', 'bras-3', capacity=self.cap['bnglink'])
        self._topo.add_edge('bras-3', 'bras-2', capacity=self.cap['bnglink'])

        self._topo.add_edge('bras-0', 'bras-4', capacity=self.cap['bnglink'])
        self._topo.add_edge('bras-4', 'bras-0', capacity=self.cap['bnglink'])

        self._topo.add_edge('bras-3', 'bras-7', capacity=self.cap['bnglink'])
        self._topo.add_edge('bras-7', 'bras-3', capacity=self.cap['bnglink'])

        self._topo.add_edge('bras-4', 'bras-5', capacity=self.cap['bnglink'])
        self._topo.add_edge('bras-5', 'bras-4', capacity=self.cap['bnglink'])

        self._topo.add_edge('bras-5', 'bras-6', capacity=self.cap['bnglink'])
        self._topo.add_edge('bras-6', 'bras-5', capacity=self.cap['bnglink'])

        self._topo.add_edge('bras-6', 'bras-7', capacity=self.cap['bnglink'])
        self._topo.add_edge('bras-7', 'bras-6', capacity=self.cap['bnglink'])

        self._topo.add_edge('bras-0', 'core-0', capacity=self.cap['bnglink'])
        self._topo.add_edge('core-0', 'bras-0', capacity=self.cap['bnglink'])

        self._topo.add_edge('bras-7', 'core-0', capacity=self.cap['bnglink'])
        self._topo.add_edge('core-0', 'bras-7', capacity=self.cap['bnglink'])

        self._topo.add_edge('src-0', 'core-0', capacity=self.cap['bnglink'])
        self._topo.add_edge('core-0', 'src-0', capacity=self.cap['bnglink'])

        # Update version id once change is done
        self._topo_version += 1

    def get_pid_topology(self):
        """Return PID based topology data in form of (vtag, [AltoPID])"""

        hasher = hashlib.sha256()
        hasher.update(str(self._topo_version).encode('ascii'))

        return (self.get_map_meta(), self._net_pids.values())

    def get_map_tag(self):
        """Get tag of a map"""
        hasher = hashlib.sha256()
        hasher.update(str(self._topo_version).encode('ascii'))

        return hasher.hexdigest()

    def get_map_meta(self):
        """Get VTAG of the map"""

        hasher = hashlib.sha256()
        hasher.update(str(self._topo_version).encode('ascii'))

        vtag = {
            'tag': hasher.hexdigest(),
            'resource-id': 'network-map'
        }

        return vtag

    def get_device_by_name(self, dev_name: str) -> NetNode:
        """Get object representing device by name"""

        # Try to get obj by name
        for dev in self._topo:
            if dev == dev_name:
                return dev            

        return None

    def get_pid_from_dev_name(self, dev_name: str) -> str:
        """Get the PID value from the given device name"""
        pass

    def get_pid_from_ip(self, ip_address) -> str:
        """Get the PID value from the given IP address"""

        # Build candidates
        candidates = []
        for pid in self._net_pids.values():
            if ip_address.version == 4:
                for prefix in pid.ipv4_prefixes:
                    if ip_address in prefix:
                        candidates.append((prefix, pid))
            elif ip_address.version == 6:
                for prefix in pid.ipv6_prefixes:
                    if ip_address in prefix:
                        candidates.append((prefix, pid))
            else:
                raise Exception('The future is here')

        # Did we find anything?
        if not any(candidates):
            return None

        # Return name of candidate with longest prefix
        (prefix, pid) = max(candidates, key=lambda x: x[0].prefixlen)
        return pid.name

    def get_device_by_ip(self, ip_address) -> NetNode:
        """Get device from given IP address"""

        # Ensure we have sane parameters
        assert (isinstance(ip_address, ipaddress.IPv4Address) or
                isinstance(ip_address, ipaddress.IPv4Address))

        # Look for a device having required ip address
        for device in self._topo:
            for ip_inf in device.ip_interfaces:
                if ip_inf.ip == ip_address:
                    return device

        # none found
        return None

    def get_upstream_router(self, device_name: str) -> str:
        """Returns first-hop upstream router. If given
        device is router - returns device_name.
        """
        
        device = None
        device = self.get_device_by_name(device_name)
        
        if device is None:
            return None
        elif device.type == 'router':
            return device.name
        #elif device.type == 'user':
        #    raise AssertionError('Upstream of {} is user: {}'.format(device_name, device))
        else:
            return self.get_upstream_router(device.upstream)

    def dev_to_dev_iterator(self, ip_a, ip_b):
        """Get iterator returning all intermediate devices in the path
        from ip_a to ip_b. First and final devices are also included.
        """
        # Create state
        device_a = self.get_device_by_ip(ip_a)
        if device_a is None:
            raise LookupError('Failed to find device having IP {}'.format(str(ip_a)))
        
        device_b = self.get_device_by_ip(ip_b)
        if device_b is None:
            raise LookupError('Failed to find device having IP {}'.format(str(ip_b)))
        
        # Set the state
        cur_device = device_a
        going_up = True
        ttl = 128

        # Special case:
        if device_a == device_b:
            yield device_a
            yield device_b
            raise StopIteration

        # Return first device
        yield device_a

        # Trace whole path
        while True:
            if cur_device.type == 'user':
                if going_up:
                    # If going up - look for upstream
                    upst_dev = self.get_device_by_name(cur_device.upstream)
                    if upst_dev is None:
                        raise LookupError('Failed to lookup upstream for device {}. Upstream: {}'
                                      .format(cur_device.name, cur_device.upstream))
                    yield upst_dev
                    # did we finish?
                    if upst_dev == device_b:
                        raise StopIteration
                    else:
                        cur_device = upst_dev
                else: # Going down
                    if cur_device == device_b:
                        yield cur_device
                        raise StopIteration
                    else:
                        raise LookupError('Going downstream but last user device is {} and not {}'
                                          .format(cur_device.name, device_b.name))

            elif cur_device.type == 'adslam':
                if going_up:
                    # If going up - look for upstream
                    upst_dev = self.get_device_by_name(cur_device.upstream)
                    if upst_dev is None:
                        raise LookupError('Failed to lookup upstream for device {}. Upstream: {}'
                                      .format(cur_device.name, cur_device.upstream))
                    yield upst_dev
                    # did we finish?
                    if upst_dev == device_b:
                        raise StopIteration
                    else:
                        cur_device = upst_dev
                else:
                    # Going down - iterate over devices
                    for (a_dev, b_dev, params) in self.get_out_edges(cur_device):
                        if b_dev == device_b:
                            yield b_dev
                            raise StopIteration
                    raise LookupError('Did not find target device attached to {}'.format(cur_device.name))

            elif cur_device.type == 'router':
                # Limit tracing length
                if ttl == 0:
                    raise LookupError('Tracing TTL exceeded')

                # Once router is found we are going "down"
                going_up = False
                
                # Did we find the target?
                if cur_device == device_b:
                    yield cur_device
                    raise StopIteration

                # Inspect RT to find outgoing interface
                rt_data = cur_device.rt_longest_prefix_match(ip_b, True)
                if rt_data is None:
                    raise LookupError('Router {} has not route to IP {}'.format(
                        cur_device.name, str(ip_b)))

                (router_intf, gw_str) = rt_data
                if gw_str == '0.0.0.0':
                    # Next device is connected directly
                    next_data = self.core_data.get_remote_peer(cur_device.name, router_intf)
                    if next_data is None:
                        raise LookupError('Failed to get device connected to {} interface {}'
                                          .format(cur_device.name, router_intf))

                    # Find next device
                    (next_hostname, next_intf) = next_data
                    next_dev = self.get_device_by_name(next_hostname)

                    # Check if it is found
                    if next_dev is None:
                        raise LookupError('Failed to find device with name {}'.format(next_hostname))

                    # Make gateway cur device
                    yield next_dev
                    ttl -= 1
                    cur_device = next_dev

                else:
                    # Get the gateway
                    gw_ip = ipaddress.ip_address(gw_str)
                    next_dev = self.get_device_by_ip(gw_ip)

                    # Check if it is found
                    if next_dev is None:
                        raise LookupError('Failed to find device with IP {}'.format(gw_str))

                    # Make gateway cur device
                    yield next_dev
                    ttl -= 1
                    cur_device = next_dev

            else:
                raise LookupError('Found device with unrecognized type {}'.format(cur_device.type))

class AltoPID(object):
    """Class representing a single ALTO PID per [RFC7285] §5.1"""

    @staticmethod
    def verify_pid_name(name):
        """Implement name verification per [RFC7285] §10.1"""

        # TODO: Do the proper implementation
        if len(name) > 64:
            return False

        return True

    def __init__(self, name, ip_prefix_list):
        """Init ALTO PID object"""

        if AltoPID.verify_pid_name(name):
            self.name = name
        else:
            raise NameError('Name format is wrong')

        self.ipv4_prefixes = []
        self.ipv6_prefixes = []

        for ip_prefix in ip_prefix_list:
            # Ensure we are not passed IPv4Interface / IPv4Address
            assert (isinstance(ip_prefix, ipaddress.IPv4Network) or
                    isinstance(ip_prefix, ipaddress.IPv6Network))

            if ip_prefix.version == 4:
                self.ipv4_prefixes.append(ip_prefix)
            elif ip_prefix.version == 6:
                self.ipv6_prefixes.append(ip_prefix)
            else:
                raise Exception('The future is here')

    def get_json_repr(self):
        """Get JSON encodable representation"""

        prefix_dict = {}

        if any(self.ipv4_prefixes):
            prefix_dict['ipv4'] = []
            for prefix in self.ipv4_prefixes:
                prefix_dict['ipv4'].append(str(prefix))

        if any(self.ipv6_prefixes):
            prefix_dict['ipv6'] = []
            for prefix in self.ipv6_prefixes:
                prefix_dict['ipv6'].append(str(prefix))

        return (self.name, prefix_dict)
