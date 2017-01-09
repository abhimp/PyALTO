import logging
import asyncio
import argparse
import os
import sys
import json
import socket
import ptvsd

import NetStatsCollector

# Enable remote execution from the Visual Studio
ptvsd.enable_attach(secret='alto')

def main(run_arg):
    """Main entry point for collector"""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
    logging.info("PyALTO NODE is starting")

    if sys.platform != 'linux' and sys.platform != 'linux2':
        logging.error('Collector supports Linux only!')
        return

    collector = NetStatsCollector.NetStatsCollector()
    
    ## Event loop
    loop = asyncio.get_event_loop()
    loop.set_debug(True)

    # Setup call to data reporting
    loop.call_later(15.0, lambda: report_stats(run_arg, collector))

    # Run until terminated
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass

    # If we are asked to close - close the connection and end the loop
    loop.close()

def report_stats(run_arg, collector):
    """Periodically report stats"""
    logging.info('Hostname: {}'.format(socket.gethostname()))
    logging.info('Adapters:')
    logging.info(collector._get_net_adapter_names())
    logging.info('Stats:')
    logging.info(collector.collect_all_interface_stats())
    logging.info('Rtable:')
    logging.info(collector.get_routing_table())

    loop = asyncio.get_event_loop()
    loop.call_later(15.0, lambda: report_stats(run_arg, collector))
    
if __name__ == "__main__":
    # Parse the command line arguments
    parser = argparse.ArgumentParser(description='ALTO Virtual Net device stats collector')

    parser.add_argument('--alto-server', help='IP Address of the ALTO server', nargs='?', default='192.168.100.100')
    parser.add_argument('--dev-type', help='Type of Virtual device (switch/router)', nargs='?', default='router')
    
    args = parser.parse_args()
    
    # Start the collector
    main(args)
