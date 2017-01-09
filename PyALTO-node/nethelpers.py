"""
A collection of functions used to collect routing information
and network link parameters of the virtual device the collector
is running on.
"""
import os
import ipaddress
import logging
import binascii
import sys
    
def get_routing_table(self):
    """Extract the node's routing table in usable format"""
        
    rt_entries = []
    first_line = True

    # Iterate over kernel's RT parsing each line
    with open('/proc/net/route', 'r') as rt_hdl:
        for rt_line in rt_hdl:
            # Skip table headers line
            if first_line:
                first_line = False
                continue
            # Skip empty lines
            elif rt_line == '\n':
                continue
            # Stop on the last line
            elif rt_line == '':
                break
            # Process entry lines
            else:
                rt_entries.append(self._parse_rt_line(rt_line))

    return rt_entries

def _parse_rt_line(self, str_line):
    """Parse a str representing a single line in rt"""

    rt_line = {}

    # Parse each token in a RT line
    for index, word in enumerate(str_line.split('\t')):
        if index == 0:
            rt_line['ifname'] = word
        elif index == 1:
            addr = int.from_bytes(binascii.unhexlify(word), sys.byteorder)
            rt_line['destination'] = str(ipaddress.IPv4Address(addr))
        elif index == 2:
            addr = int.from_bytes(binascii.unhexlify(word), sys.byteorder)
            rt_line['gateway'] = str(ipaddress.IPv4Address(addr))
        elif index == 3:
            int_flags = int(word)
            flags = []
            if int_flags & 0b00000001:
                flags.append('U')
            if int_flags & 0b00000010:
                flags.append('G')
            rt_line['flags'] = flags
        elif index == 4:
            rt_line['refcnt'] = int(word)
        elif index == 5:
            rt_line['use'] = int(word)
        elif index == 6:
            rt_line['metric'] = int(word)
        elif index == 7:
            addr = int.from_bytes(binascii.unhexlify(word), sys.byteorder)
            rt_line['mask'] = str(ipaddress.IPv4Address(addr))
        elif index == 8:
            rt_line['mtu'] = int(word)
        elif index == 9:
            rt_line['window'] = int(word)
        elif index == 10:
            rt_line['irtt'] = int(word)
        else:
            logging.error('Unexpected number of RT line tokens!')

    return rt_line

def collect_all_interface_stats(self):
    """Collect and return stats of all interfaces"""

    # Get the list of active adapters
    interfaces = self.get_net_adapter_names()

    # Get the adapter stats
    interface_stats = [self._get_interface_stats(iname) for iname in interfaces]
        
    return interface_stats


def _get_interface_stats(self, interface_name):
    """Collect and return stats of the given interface"""
                
    # Holder of stat data
    stat_data = {
        'name': interface_name,
        'stats': {},
    }

    # Build path to the files holding stats
    stat_dir = os.path.join(
        os.path.join('/sys/class/net/', interface_name),
        'statistics')
                
    # Collect the statistical values
    for stat in os.listdir(stat_dir):
        stat_path = os.path.join(stat_dir, stat)
        with open(stat_path, 'r') as stat_file_hdl:
            stat_data['stats'][stat] = int(stat_file_hdl.read())

    # Return the collected data
    return stat_data

def get_net_adapter_names(self):
    """Get the names of network adapters"""
        
    # Iterate over adapter names and skip loopback
    sys_dir = '/sys/class/net'
    interface_names = [iname for iname in os.listdir(sys_dir) if iname != 'lo']

    return interface_names
