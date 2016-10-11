import ipaddress

import networkx as nx

class AltoPID(object):
    """Representation of the ALTO PID entry"""
    def __init__(self, name, ip_prefixes):
        self.name = name
        self.ip_prefixes = ip_prefixes

class NetworkMap(object):
    """Representation of the physical network"""

    def __init__(self):
        """Create in-memory representation of our network"""
        self._build_static_topology()

    def get_map_meta(self):
        """Return the version of the map"""

        v = {}
        v['vtag'] = {}
        v['vtag']['resource-id'] = "default-static-network-map"
        v['vtag']['tag'] = "1"

        return v

    def get_network_pids(self):
        """Build the list of all network PIDs"""
        return self._pids
       
    def _build_static_topology(self):
        """Build the hardcoded topology.
           This method can be overridden to load topo from file
           or some other external interface.
        """

        # We need Multi (one edge for each direction), Directed (flows in and out), Graph
        self._network_graph = nx.MultiDiGraph()

        dslam_list = ["adslam0", "adslam1", "adslam2", "adslam3"]
        access_routers_list = ["access0", "access1"]
        core_routers_list = ["core0", "core1"]
        home_nodes_list = []

        for i in range(0, 24):
            home_nodes_list.append("home"+str(i))

        self._network_graph.add_nodes_from(dslam_list)
        self._network_graph.add_nodes_from(access_routers_list)
        self._network_graph.add_nodes_from(core_routers_list)
        self._network_graph.add_nodes_from(home_nodes_list)

        # Build PIDs
        self._pids = []
        self._pids.append(AltoPID(
            "pid-access0", 
            [ipaddress.IPv4Network("10.0.0.0/26")]))
        self._pids.append(AltoPID(
            "pid-access1", 
            [ipaddress.IPv4Network("10.0.0.64/26")]))
        self._pids.append(AltoPID(
            "pid-datacenter0",
            [ipaddress.IPv4Network("10.0.102.0/24")]))
        self._pids.append(AltoPID(
            "pid-isp0",
            [ipaddress.IPv4Network("10.0.0.0/8")]))