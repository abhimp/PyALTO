import logging
import asyncio
import os
import ipaddress
import binascii
import socket
import sys
import getopt
import json
import datetime

from Framer import Framer

class CollectorClientProto(asyncio.Protocol):
    """Asyncio client protocol implementation"""
    def __init__(self):
        self._transport = None
        self._framer = Framer(self.OnData)
        self._loop = asyncio.get_event_loop()
        self._refresh_hdl = None
        return

    def connection_made(self, transport):
        logging.info("Connection to ALTO server established")
        self._transport = transport
        self.RegisterWithServer()
        return

    def connection_lost(self, exc):
        logging.warn("Connection to ALTO server lost: {0}"
                     .format(exc))
        return

    def data_received(self, data):
        self._framer.DataReceived(data)
        return

    def CloseConnection(self):
        self._transport.close()
        self._transport = None
        return

    def SendData(self, data):
        obj_bytes = json.dumps(data).encode()
        self._transport.write(self._framer.Frame(data)) 

    def OnData(self, data):
        data_obj = json.loads(data.decode())
        return

    def RegisterWithServer(self):
    
        self._rt = GetRoutingTable()
        self._interfaces = set([x['iface'] for x in rt])
        ifs_stats = GetIfaceStats(self._interfaces)
        ts = int(time.time()) 

        data = {}
        data['type'] = 'register'
        data['rtable'] = self._rt
        data['stats'] = ifs_stats
        data['timestamp'] = ts

        SendData(data)

        logging.info("Sent ALTO registration message")

        return


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

    # Get the routing table
    #rt = GetRoutingTable()
    # Get unique interfaces
    #ifs = set([x['iface'] for x in rt])
    # Get interface stats
    #ifs_stats = GetIfaceStats(ifs)
    alto_ip = ''

    try:
        opts, args = getopt.getopt(argv, "s", ["server="])
    except getopt.GetoptError:
        logging.critical("Error parsing cmd line arguments")
        sys.exit(1)

    for opt, arg in opts:
        if opt in ('-s', '--server'):
            alto_ip = arg

    logging.info("Connecting to ALTO server at {0}".format(alto_ip))

    # Event loop
    loop = asyncio.get_event_loop()
    loop.set_debug(True)
    coro = loop.create_connection(CollectorClientProtocol, alto_ip, 6776)
    transport, server = loop.run_until_complete(coro)

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass

    # If we are asked to close - close the connection and end the loop
    server.CloseConnection()
    loop.close()

if __name__ == "__main__":
    main(sys.argv[1:])
