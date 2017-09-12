"""
PyALTO, a Python3 implementation of Application Layer Traffic Optimization protocol
Copyright (C) 2016,2017  J. Poderys, Technical University of Denmark

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

"""
Implementation of ALTO protocol
"""
import ipaddress
import logging

from altoserver import nm

class AltoServer(object):
    """This class implementes functionality of the ALTO protocol"""

    def __init__(self):
        """Initialize the ALTO server"""

        self._cost_providers = []
        self._property_providers = []
        self._address_parsers = []

    def parse_endpoints(self, in_endpoints):
        """Parse textual address representations to Python objects"""

        assert any(in_endpoints)

        results = []

        # Iterate over all addresses
        for address in in_endpoints:

            assert address.count(':') == 1
            (addr_type, addr) = address.split(':')

            parser = self._get_address_parser(addr_type)
            if parser is None:
                logging.info('Did not find parser for type: {}'.format(addr_type))
                continue

            parsed_addr = parser.to_object(address)
            if parsed_addr is None:
                logging.info('Failed to parse address: {}'.format(address))
                continue

            results.append(parsed_addr)

        # Return results
        return results

    def get_network_map(self):
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

        assert any(properties) and any(endpoints)

        # Parse addresses from 'type:addr' to Python objects
        parsed_addr = self.parse_endpoints(endpoints)

        endp_props = {}
        dependent_tags = []
        
        # Iterate over addresses.
        # For each address we have to get all properties
        for address in parsed_addr:

            props = {}
            
            for property in properties:
                
                provider = self._get_property_provider(property)
                if provider is None:
                    logging.info('No property provider for {} property'.format(property))
                    continue
                    
                property_val = provider.get_property(address)
                if property_val is None:
                    logging.info('Property {} not processed for address: {}'
                                 .format(property, str(address)))
                    continue

                # Save values
                (prop_value, dependency) = property_val
                props[property] = prop_value
                dependent_tags.append(dependency)

            # Link address to all properties if any
            if any(props.keys()):
                endp_props[address] = props

        # Change from object to string
        keys_copy = list(endp_props.keys())
        for key in keys_copy:
            parser = self._get_address_parser(key)
            new_key = parser.from_object(key)
            endp_props[new_key] = endp_props.pop(key)

        # Ensure no duplicate dependent vtags
        no_dupes  = [dict(t) for t in set([tuple(d.items()) for d in dependent_tags])]

        resp = {
            'meta' : {
                'dependent-vtags' : no_dupes
            },
            'endpoint-properties' : endp_props
        }
        
        return resp

    def get_endpoint_costs(self, cost_type, endpoints):
        """Implement cost calculation service by given endpoints"""

        # Get cost estimator based on cost type parameter
        cost_estimator = self._get_cost_estimator(
            cost_type['cost-mode'], 
            cost_type['cost-metric']
        )

        # Get costs provided by cost estimator
        cost_map = cost_estimator.get_cost(endpoints['srcs'], endpoints['dsts'])
        
        costmap_response = {
            'meta' : {
                'cost-type' : cost_type
            },
            'endpoint-cost-map': cost_map
        }

        return costmap_response

    def register_address_parsers(self, addr_parsers):
        """Register given parsers with the server"""
        assert any(addr_parsers)

        for parser in addr_parsers:
            self._address_parsers.append(parser)

    def register_property_providers(self, prop_provider):
        """Register given property providers with the server"""
        assert any(prop_provider)

        for provider in prop_provider:
            self._property_providers.append(provider)

    def register_cost_providers(self, cost_providers):
        """Register given cost providers with the ALTO server"""
        assert any(cost_providers)

        for provider in cost_providers:
            self._cost_providers.append(provider)

    def _get_cost_estimator(self, cost_mode, cost_metric):
        """Factory method to return registered cost estimator"""

        for cost_provider in self._cost_providers:
            if (cost_provider.cost_mode == cost_mode and
                cost_provider.cost_metric == cost_metric):
                return cost_provider

        return None

    def _get_property_provider(self, property_name):
        """Factory method to return endpoint property provider"""

        # Find provider for given property
        for provider in self._property_providers:
            if provider.property_name == property_name.lower():
                return provider

        # No providers found
        return None

    def _get_address_parser(self, address):
        """Get address parser from address type"""

        # Two ways lookup
        if isinstance(address, str):
            for parser in self._address_parsers:
                if address in parser.identifiers:
                    return parser
        else:
            for parser in self._address_parsers:
                if type(address) in parser.types:
                    return parser
        # No parsers
        return None
