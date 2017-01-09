import logging
import asyncio
import argparse
import os
import sys
import json
import socket
import ptvsd

import nethelpers

# Enable remote execution from the Visual Studio
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
    loop.call_later(run_args['collect-interval'], report_stats, run_args)

    # Run until terminated
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass

    # If we are asked to close - close the connection and end the loop
    loop.close()

def report_stats(run_args):
    """Periodically report stats"""
    logging.info('Hostname: {}'.format(socket.gethostname()))
    logging.info('Adapters:')
    logging.info(nethelpers.get_net_adapter_names())
    logging.info('Stats:')
    logging.info(nethelpers.collect_all_interface_stats())
    logging.info('Rtable:')
    logging.info(nethelpers.get_routing_table())

    loop = asyncio.get_event_loop()
    loop.call_later(run_args['collect-interval'], report_stats, run_args)
    
if __name__ == "__main__":
    # Parse the command line arguments
    parser = argparse.ArgumentParser(description='ALTO Virtual Net device stats collector')

    parser.add_argument('--alto-server', help='IP Address of the ALTO server', nargs='?', default='192.168.100.100')
    parser.add_argument('--dev-type', help='Type of the virtual device (switch/router)', nargs='?', default='router')
    parser.add_argument('--collect-interval', help='Data collection frequency', nargs='?', default=15.0)
    
    args = parser.parse_args()
    
    # Start the collector
    main(args)
