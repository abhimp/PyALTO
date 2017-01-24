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
import subprocess
    
def get_routing_table():
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
                rt_entries.append(_parse_rt_line(rt_line))

    return rt_entries

def _parse_rt_line(str_line):
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

def collect_all_interface_stats():
    """Collect and return stats of all interfaces"""

    # Get the list of active adapters
    interfaces = get_net_adapter_names()

    # Get the adapter stats
    interface_stats = [_get_interface_stats(iname) for iname in interfaces]
        
    return interface_stats


def _get_interface_stats(interface_name):
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

def get_net_adapter_names():
    """Get the names of network adapters"""
        
    # Iterate over adapter names and skip loopback
    sys_dir = '/sys/class/net'
    interface_names = [iname for iname in os.listdir(sys_dir) if iname != 'lo']

    return interface_names

def get_quagga_rt():
    """Extract routing table as seen by Quagga"""

    # Get Quagga RT
    with subprocess.Popen(
            ['vtysh -c \"sh ip route\"'],
            stdout=subprocess.PIPE,
            shell=True,
            universal_newlines=True) as p_vtysh:
        
        quagga_rt = p_vtysh.stdout.readlines()

    # Strip the newlines
    lines = [line.replace('\n','') for line in quagga_rt]

    # Return nothing if not enough lines
    if len(lines) < 5:
        return None

    # Process Quagga lines
    return _process_quagga_rt(lines)

def _process_quagga_rt(in_lines):
    """Process quagga lines"""
    
    # Format
    #{
    #    'protocol': '',
    #    'selected': True|False,
    #    'fib': True|False,
    #    'subnet': '',
    #    'AD': 0|None,
    #    'RD': 0|None,
    #    'GW': ipaddress|None,
    #    'Int': ''
    #}

    out = []

    # Some lines might refer to the previous line
    # so we need to keep state
    last_proto = None
    last_subnet = None
    last_ad = None
    last_rd = None

    # Process the output
    for lineno, line in enumerate(lines):
        # Skip headers
        if lineno in [0, 1, 2, 3]:
            continue

        # Process the lines
        # Type Code
        if line[0] == ' ':
            proto = last_proto
        else:
            proto = line[0]

            # Code present, clear cache
            last_proto = None
            last_subnet = None
            last_ad = None
            last_rd = None

        # Selected
        if line[1] == '>':
            selected = True
        else:
            selected = False

        # FIB
        if line[2] == '*':
            fib = True
        else:
            fib = False

        # Handle differently if Routing proto or Directly connected
        tokens = line.split(' ')
        if proto == 'C':
            # Look for anchor 'is'. -1 is subnet, +3 is adapter
            for num, token in enumerate(tokens):
                if token == 'is':
                    subnet = c_tokens[num-1]
                    last_subnet = subnet
                    adapter = c_tokens[num+3]
                    ad = None
                    rd = None
                    gw = None
                    break
                else:
                    continue
        else:
            # Look for anchor 'via'.
            for num, token in enumerate(tokens):
                if token == 'via':
                    if proto == ' ':
                        # Load cached
                        subnet = last_subnet
                        ad = last_ad
                        rd = last_rd
                    else:
                        # Parse flieds before 'via'
                        subnet = rp_tokens[num-2]
                        last_subnet = subnet
                        (ad, rd) = rp_tokens[num-1].strip('[]').split('/')
                        ad = int(ad)
                        rd = int(rd)
                        last_ad = ad
                        last_rd = rd

                    gw = rp_tokens[num+1].strip(',')
                    adapter = rp_tokens[num+2].strip(',')
                    break
                else:
                    continue
        
        out.append({
            'protocol': proto,
            'selected': selected,
            'fib': fib,
            'subnet': subnet,
            'AD': ad,
            'RD': rd,
            'GW': gw,
            'Int': adapter
        })

    # Return data
    return out
