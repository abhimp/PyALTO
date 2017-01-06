import logging
import asyncio
import os
import ipaddress
import binascii
import sys
import json
import datetime
import ptvsd
import argparse

import NetStatsCollector

# Enable remote execution from the Visual Studio
ptvsd.enable_attach(secret='alto')

# Create a TCP connection to the ALTO server
def GetIfaceStats(ifaces):
    """Get stats of each iface"""
    stats = {}
    for iface in ifaces:
        stats_dict = {}
        stat_dir = os.path.join(os.path.join('/sys/class/net', iface), 'statistics')
        for stat in os.listdir(stat_dir):
            stat_path = os.path.join(stat_dir, stat)
            fp = open(stat_path, 'r')
            stats_dict[stat] = int(fp.read())
        stats[iface] = stats_dict

    return stats


def GetRoutingDetails():
    """Get kernel routing table"""
    rt = open('/proc/net/route', 'r')
    
    rtable = []
    lnnum = 0
    while True:
        # Skip line with headings
        ln = rt.readline()
        if lnnum == 0:
            #print(ln)
            lnnum = lnnum + 1
            continue

        # Read lines until the end
        if ln == None or ln == '':
            break
        else:
            lnnum = lnnum + 1

        item = 0
        line = {}

        # Parse each column
        for word in ln.split('\t'):
            if item == 0:
                line['iface'] = word
            elif item == 1:
                addr = int.from_bytes(binascii.unhexlify(word), sys.byteorder)
                ip = ipaddress.IPv4Address(addr)
                line['destination'] = ip
            elif item == 2:
                addr = int.from_bytes(binascii.unhexlify(word), sys.byteorder)
                ip = ipaddress.IPv4Address(addr)
                line['gateway'] = ip
            elif item == 3:
                int_fl = int(word)
                arr_fl = []
                if int_fl & 0b00000001:
                    arr_fl.extend('U')
                if int_fl & 0b00000010:
                    arr_fl.extend('G')
                line['flags'] = arr_fl
            elif item == 4:
                line['refcnt'] = word
            elif item == 5:
                line['use'] = word
            elif item == 6:
                line['metric'] = int(word)
            elif item == 7:
                addr = int.from_bytes(binascii.unhexlify(word), sys.byteorder)
                ip = ipaddress.IPv4Address(addr)
                line['mask'] = ip
            elif item == 8:
                line['mtu'] = int(word)
            elif item == 9:
                line['window'] = int(word)        
            elif item == 10:
                line['irtt'] = int(word.strip())
            item = item + 1

        # add line to the table
        rtable.append(line)

    # Return the table
    return rtable

def main(argv):
    """Main entry point for collector"""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
    logging.info("PyALTO NODE is starting")

    if sys.platform != 'linux' and sys.platform != 'linux2':
        logging.error('Collector supports Linux only!')
        return

    nsc = NetStatsCollector.NetStatsCollector()

    ## Event loop
    loop = asyncio.get_event_loop()
    loop.set_debug(True)

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass

    # If we are asked to close - close the connection and end the loop
    loop.close()

if __name__ == "__main__":
    # Parse the command line arguments
    parser = argparse.ArgumentParser(description='ALTO Virtual Net device stats collector')

    parser.add_argument('--alto-server', help='IP Address of the ALTO server', nargs='?', default='192.168.100.100')
    parser.add_argument('--dev-type', help='Type of Virtual device (switch/router)', nargs='?', default='router')
    
    args = parser.parse_args()
    
    # Start the collector
    main(args)
