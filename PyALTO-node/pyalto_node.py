"""
Collector program to upload data from virtual routers/switches to ALTO server.
"""
import logging
import asyncio
import argparse
import sys
import socket
import ptvsd
import requests

import nethelpers

# Enable remote execution from the Visual Studio
# ! Comment out this line if running locally on Win PC!
ptvsd.enable_attach(secret='alto')

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

    # Make base URL
    server_url = 'http://' + run_args.alto_server + '/upload/' + socket.gethostname() + '/'

    # POST adapeter counters
    adapter_stats = nethelpers.collect_all_interface_stats()
    requests.post(server_url + 'adapter_stats', json=adapter_stats)

    # POST adapter addresses
    adapter_addresses = nethelpers.get_interfaces_addresses()
    requests.post(server_url + 'adapter_addr', json=adapter_stats)

    # If this is router POST routing table
    if run_args.dev_type == 'router':
        rtable = nethelpers.get_routing_table()
        requests.post(server_url + 'rtable', json=rtable)

        quagga_rt = nethelpers.get_quagga_rt()
        requests.post(server_url + 'quagga_rt', json=quagga_rt)

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
