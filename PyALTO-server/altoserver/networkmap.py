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

    def init_simple_topo(self):
        """Create a simple topology for testing"""

        # Add two nodes
        dev_names = ['core-dev', 'r2']
        for dn in dev_names:
            node = NetNode(dn, 'router')
            self._topo.add_node(node)

        self.add_pid_to_topology(
            'home-0',
            [ipaddress.IPv4Network('192.168.0.0/24')]
        )

        self.add_pid_to_topology(
            'home-1',
            [ipaddress.IPv4Network('192.168.1.0/24')]
        )

        self.add_pid_to_topology(
            'home-2',
            [ipaddress.IPv4Network('192.168.2.0/24')]
        )

        self.add_pid_to_topology(
            'home-3',
            [ipaddress.IPv4Network('192.168.3.0/24')]
        )

        self.add_pid_to_topology(
            'dc-0',
            [ipaddress.IPv4Network('192.168.100.0/24'),
             ipaddress.IPv4Network('192.168.102.0/24'),]
        )

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

    def get_device(self, dev_name):
        """Get object representing device by name"""

        # Try to get obj by name
        try:
            dev = self._topo[dev_name]
        except:
            # There is no such device
            return None

        # Return the device
        return dev

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
        (prefix, pid) = min(candidates, key=lambda x: x[0].prefixlen)
        return pid.name


class AltoPID(object):
    """Class representing a single ALTO PID per [RFC7285] §5.1"""

    def __init__(self, name, ip_prefix_list):
        """Init ALTO PID object"""

        if self._verify_pid_name(name):
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

    def _verify_pid_name(self, name):
        """Implement name verification per [RFC7285] §10.1"""

        # TODO: Do the proper implementation
        if len(name) > 64:
            return False

        return True

    def get_json_repr(self):
        """Get JSON encodable representation"""

        repr = {}

        if any(self.ipv4_prefixes):
            repr['ipv4'] = []
            for prefix in self.ipv4_prefixes:
                repr['ipv4'].append(str(prefix))

        if any(self.ipv6_prefixes):
            repr['ipv6'] = []
            for prefix in self.ipv6_prefixes:
                repr['ipv6'].append(str(prefix))

        return (self.name, repr)
