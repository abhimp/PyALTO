"""
Implementation of ALTO protocol
"""
import ipaddress

from altoserver.networkmap import AltoPID
from altoserver import nm

class AltoServer(object):
    """This class implementes functionality of the ALTO protocol"""

    @staticmethod
    def parse_endpoints(in_endpoints):
        """Parse each endpoint to IPv4/v6 address.
           Supports IPv4 and IPv6 address types.        
        """

        results = []

        # Iterate over all addresses
        for address in in_endpoints:
            (addr_type, addr) = address.split(':')

            if addr_type.lower() == 'ipv4' or addr_type.lower() == 'ipv6':
                results.append(ipaddress.ip_address(addr))

            # Check for any other address type here

        # Return results
        return results

    def get_network_map():
        """Return JSON serializable network map per [RFC7285] p11.2.1"""
    
        # Get internal network representation
        (meta, map) = nm.get_pid_topology()

        # Add pids
        nmap = {}
        for pid in map:
            (name, data) = pid.get_json_repr()
            nmap[name] = data
    
        # Build the response
        resp = {
            'meta': meta,
            'network-map': nmap
        }

        return resp

    def get_endpoint_properties(self, properties, endpoints):
        """Return endpoint properties [RFC7285] p 11.4.1"""
        # IMHO no need to handle error cases, let exceptions
        # propagate and fail back to client

        # TODO: Implement pluggable properties and endpoint parsers
        # For now return PID only (p 11.4.1.4)

        parsed_addr = AltoServer.parse_endpoints(endpoints)

        endp_props = {}
        
        # Iterate over addresses
        for address in parsed_addr:

            props = {}

            # TODO: Use factory pattern here
            for property in properties:
                if property == 'network-map.pid':
                    pid = nm.get_pid_from_ip(address)
                    if pid is not None:
                        props['network-map.pid'] = pid
                else:
                    raise NotImplementedError('Unknown property: {}'.format(property))
        
            if address.version == 4:
                addr_str = 'ipv4:' + str(address)
            else:
                addr_str = 'ipv6:' + str(address)

            endp_props[addr_str] = props

        # Build and return response
        # TODO: Dependent resources should be dynamic
        resp = {
            'meta' : {
                'dependent-vtags': [
                    { 
                        'resource-id' : 'network-map',
                        'tag' : nm.get_map_tag()
                    }
                ]
            },
            'endpoint-properties' : endp_props
        }

        return  resp
