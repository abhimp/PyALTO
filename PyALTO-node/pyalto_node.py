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
Collector program to upload data from virtual routers/switches to ALTO server.
"""
import logging
import asyncio
import argparse
import sys
import socket
#import ptvsd
import requests
import traceback

import nethelpers

# Enable remote execution from the Visual Studio
# ! Comment out this line if running locally on Win PC!
#ptvsd.enable_attach(secret='alto')

def main(run_args):
    """Main entry point for collector"""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
    logging.info("PyALTO NODE is starting")

    if sys.platform != 'linux' and sys.platform != 'linux2':
        logging.error('Collector supports Linux only!')
        return

    ## Event loop
    loop = asyncio.get_event_loop()
    loop.set_debug(True)

    # Setup call to data reporting
    loop.call_later(run_args.collect_interval, report_stats, run_args)

    # Run until terminated
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass

    # If we are asked to close - close the connection and end the loop
    loop.close()

def report_stats(run_args):
    """Periodically report stats"""
    try:
        # Make base URL
        server_url = 'http://' + run_args.alto_server + '/upload/' + socket.gethostname() + '/'

        # POST adapeter counters
        adapter_stats = nethelpers.collect_all_interface_stats()
        requests.post(server_url + 'adapter_stats', json=adapter_stats)

        # POST adapter addresses
        adapter_addresses = nethelpers.get_interfaces_addresses()
        requests.post(server_url + 'adapter_addr', json=adapter_addresses)

        # If this is router POST routing table
        if run_args.dev_type == 'router':
            rtable = nethelpers.get_routing_table()
            requests.post(server_url + 'rtable', json=rtable)

            quagga_rt = nethelpers.get_quagga_rt()
            if quagga_rt is not None:
                requests.post(server_url + 'quagga_rt', json=quagga_rt)
    
    # Consume OSError when remote is not answering
    except OSError as exc:
        logging.error('Consumed OSError: %s', exc)

    # Schedule next run
    loop = asyncio.get_event_loop()
    loop.call_later(run_args.collect_interval, report_stats, run_args)

if __name__ == "__main__":
    # Parse the command line arguments
    parser = argparse.ArgumentParser(description='ALTO Virtual Net device stats collector')

    parser.add_argument('--alto-server', help='IP Address of the ALTO server', default='127.0.0.1')
    parser.add_argument('--dev-type', help='Type of the virtual device (switch/router)', default='router')
    parser.add_argument('--collect-interval', help='Data collection frequency', default=15.0)

    args = parser.parse_args()

    # Start the collector
    main(args)
