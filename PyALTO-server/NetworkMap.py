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

    def get_map_vtag(self):
        """Return the version of the map"""

        v = {
            'resource-id': "default-static-network-map",
            'tag' : "1"
        }

        return v

    def get_network_pids(self):
        """Build the list of all network PIDs"""
        return self._pids

    def get_numerical_routingcost(self):
        return self._pid_routing_cost

    def _get_pid_by_name(self, pid_name):
        """Return PID object by given name"""
        for p in self._pids:
            if p.name == pid_name:
                return p

        return None
       
    def _build_static_topology(self):
        """Build the hardcoded topology.
           This method can be overridden to load topo from file
           or some other external interface.
        """

        # We need Multi (one edge for each direction), Directed (flows in and out), Graph
        self._network_graph = nx.MultiDiGraph()

        dslam_list = ["adslam0", "adslam1", "adslam2", "adslam3", "adslam4", "adslam5", "adslam6", "adslam7"]
        access_routers_list = ["access0", "access1", "access2", "access3"]
        core_routers_list = ["core0", "core1"]
        home_nodes_list = []

        for i in range(0, 48):
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
            "pid-access2", 
            [ipaddress.IPv4Network("10.0.0.128/26")]))
        self._pids.append(AltoPID(
            "pid-access3", 
            [ipaddress.IPv4Network("10.0.0.192/26")]))
        self._pids.append(AltoPID(
            "pid-datacenter0",
            [ipaddress.IPv4Network("10.0.102.0/24")]))
        #self._pids.append(AltoPID(
        #    "pid-isp0",
        #    [ipaddress.IPv4Network("10.0.0.0/8")]))

        # As number of router hops between the PIDS
        self._pid_routing_cost = {}
        self._pid_routing_cost[self._get_pid_by_name("pid-access0")] = {
            self._get_pid_by_name("pid-access0"): 1,
            self._get_pid_by_name("pid-access1"): 2,
            self._get_pid_by_name("pid-access2"): 3,
            self._get_pid_by_name("pid-access3"): 3,
            self._get_pid_by_name("pid-datacenter0"): 2 
            }
        self._pid_routing_cost[self._get_pid_by_name("pid-access1")] = {
            self._get_pid_by_name("pid-access0"): 2,
            self._get_pid_by_name("pid-access1"): 1,
            self._get_pid_by_name("pid-access2"): 3,
            self._get_pid_by_name("pid-access3"): 3,
            self._get_pid_by_name("pid-datacenter0"): 2 
            }
        self._pid_routing_cost[self._get_pid_by_name("pid-access2")] = {
            self._get_pid_by_name("pid-access0"): 3,
            self._get_pid_by_name("pid-access1"): 2,
            self._get_pid_by_name("pid-access2"): 1,
            self._get_pid_by_name("pid-access3"): 2,
            self._get_pid_by_name("pid-datacenter0"): 2 
            }
        self._pid_routing_cost[self._get_pid_by_name("pid-access3")] = {
            self._get_pid_by_name("pid-access0"): 3,
            self._get_pid_by_name("pid-access1"): 3,
            self._get_pid_by_name("pid-access2"): 2,
            self._get_pid_by_name("pid-access3"): 1,
            self._get_pid_by_name("pid-datacenter0"): 2 
            }
        self._pid_routing_cost[self._get_pid_by_name("pid-datacenter0")] = {
            self._get_pid_by_name("pid-access0"): 2,
            self._get_pid_by_name("pid-access1"): 2,
            self._get_pid_by_name("pid-access2"): 2,
            self._get_pid_by_name("pid-access3"): 2,
            self._get_pid_by_name("pid-datacenter0"): 1 
            }
