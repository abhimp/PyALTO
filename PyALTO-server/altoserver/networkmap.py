"""
Classes related to network topology capture and representation.
"""
import ipaddress
import hashlib

from networkx import nx
from altoserver.netnode import NetNode

class NetworkMap(object):
    """Holder of network topology"""

    def __init__(self):
        """Initialize the network topology"""

        # Topology as MultiDiGraph (MultiDi - Since each link is two unidirectional edges)
        self._topo = nx.MultiDiGraph()
        self._net_pids = {}             # Pin_Name -> Pid object
        self._topo_version = 0          # Each topology change should change the version number

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
        core = NetNode('core-0', 'router')
        self._topo.add_node(core)
        self.add_pid_to_topology('core-dc', [
            ipaddress.ip_interface('192.168.240.0/24'),
            ipaddress.ip_interface('192.168.245.0/24')
        ])

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
                self._topo.add_edge(adslam, bras)
                self._topo.add_edge(bras, adslam)

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
                    self._topo.add_edge(home, adslam)
                    self._topo.add_edge(adslam, home)

                # Add pid representing ADSLAM
                self.add_pid_to_topology(adslam_name, [adslam_net])

        # connect BRAS/CORE
        self._topo.add_edge('bras-0', 'bras-1')
        self._topo.add_edge('bras-1', 'bras-0')

        self._topo.add_edge('bras-1', 'bras-2')
        self._topo.add_edge('bras-2', 'bras-1')

        self._topo.add_edge('bras-0', 'bras-2')
        self._topo.add_edge('bras-2', 'bras-0')

        self._topo.add_edge('bras-0', 'core-0')
        self._topo.add_edge('core-0', 'bras-0')

        self._topo.add_edge('bras-2', 'core-0')
        self._topo.add_edge('core-0', 'bras-2')


    def init_simple_topo(self):
        """Create a simple topology for testing"""

        # For use by dev machine
        core = NetNode('core-dev', 'router')
        self._topo.add_node(core)

        # ADSLAM user's IPs are:
        # 192.168.<ADSLAM_ID>.<USER_ID+2>/24 (USER_ID=1 reserved for router)
        num_bras = 6
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
                self._topo.add_edge(adslam, bras)
                self._topo.add_edge(bras, adslam)

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
                    self._topo.add_edge(home, adslam)
                    self._topo.add_edge(adslam, home)

                # Add pid representing ADSLAM
                self.add_pid_to_topology(adslam_name, [adslam_net])

        # Interconnect BRASes
        self._topo.add_edge('bras-0', 'bras-1')
        self._topo.add_edge('bras-1', 'bras-0')

        self._topo.add_edge('bras-1', 'bras-2')
        self._topo.add_edge('bras-2', 'bras-1')

        self._topo.add_edge('bras-0', 'bras-3')
        self._topo.add_edge('bras-3', 'bras-0')

        self._topo.add_edge('bras-2', 'bras-5')
        self._topo.add_edge('bras-5', 'bras-2')

        self._topo.add_edge('bras-3', 'bras-4')
        self._topo.add_edge('bras-4', 'bras-3')

        self._topo.add_edge('bras-4', 'bras-5')
        self._topo.add_edge('bras-5', 'bras-4')

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

    def get_device_by_name(self, dev_name):
        """Get object representing device by name"""

        # Try to get obj by name
        for dev in self._topo:
            if dev == dev_name:
                return dev            

        return None

    def get_pid_from_dev_name(self, dev_name):
        """Get the PID value from the given device name"""
        pass

    def get_pid_from_ip(self, ip_address):
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

    def get_device_by_ip(self, ip_address):
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
