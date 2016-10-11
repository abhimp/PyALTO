class AltoService(object):
    """Implementation of the ALTO service
       as described in RFC7285. This class
       ascts as a glue logic and data-transformer
       between different modules (classes).
    """

    def get_network_map(self):
        """Return the network map [RFC7285 11.2.1]"""

        # Get map's details
        vtag = self._ms.get_map_vtag()
        pids = self._ms.get_network_pids()

        # Transform PIDs to the network map
        map = {}
        for p in pids:
            map[p.name] = {}

            ipv4_networks = []
            ipv6_networks = []

            # Iterate over the prefixes and put into ip-type bins
            for prefix in p.ip_prefixes:
                if prefix.version == 4:
                    ipv4_networks.append(prefix.compressed)
                elif prefix.version == 6:
                    ipv6_networks.append(prefix.compressed)
            
            if len(ipv4_networks) > 0:
                map[p.name]['ipv4'] = ipv4_networks
            if len(ipv6_networks) > 0:
                map[p.name]['ipv6'] = ipv6_networks

        # Get the map
        nm = {
            'meta': {
                'vtag': vtag}, 
            'network-map': map}

        # Give back the data structure for delivery
        return nm

    def get_cost_map(self, mode, metric):
        if mode == "ordinal":
            return None
        if metric != "routingcost":
            return None

        # Get map's meta
        vtag = self._ms.get_map_vtag()
        nr = self._ms.get_numerical_routingcost()

        # costmap type
        cmt = {
            "cost-mode": mode,
            "cost-metric": metric}

        # Transform into ALTO notation from Objects
        nrep = {}
        for pid_from, costs in nr.items():
            rcosts = {}
            for to_pid, cost in costs.items():
                rcosts[to_pid.name] = cost
            nrep[pid_from.name] = rcosts

        # Build the response
        cm = {"meta" : {
                "dependent-vtags" : [vtag]},
              "cost-type": cmt,
              "cost-map": nrep}
        return cm

    def register_map_service(self, ms):
        """Register the map service
           with the ALTO Service
        """
        self._ms = ms

