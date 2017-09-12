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
import shlex

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

def get_interfaces_addresses():
    """Collect interface address details"""

    # Get the liost of active interfaces
    interfaces = get_net_adapter_names()

    # Loop over all interfaces collecting all addresses
    if_details = {}
    for iface in interfaces:
        if_details[iface] = _get_iface_addr(iface)

    return if_details

def _get_iface_addr(iface):
    """Extract iface addr details from ip utility"""

    # Get Quagga RT
    shl = shlex.split('ip -a -d -o addr list {}'.format(iface))
    with subprocess.Popen(
        shl,
        stdout=subprocess.PIPE,
        #shell=True,
        universal_newlines=True) as popen_ip:

        ip_addr_data = popen_ip.stdout.readlines()

    # Strip the newlines
    lines = [line.replace('\n', '') for line in ip_addr_data]

    # Parse all line
    parsed_data = [_parse_ip_addr_single_line(line) for line in lines]

    return parsed_data

def _parse_ip_addr_single_line(line):
    """Parse a single line from ip addr list command"""

    data = {
        'id': None,
        'name': '',
        'family': '',
        'address': '',
        'brd': '',
        'scope': '',
        'valid_left': None,
        'preferred_left': None
    }

    # Split into to blocks
    (block1, block2) = line.split('\\')

    # Process block one
    tokens = block1.split(' ')

    data['id'] = tokens[0].strip(':')
    data['name'] = tokens[1]
    data['family'] = tokens[5]
    data['address'] = tokens[6]

    for key, token in enumerate(tokens):
        if token == 'brd':
            data['brd'] = tokens[key+1]

        if token == 'scope':
            data['scope'] = tokens[key+1]

    # Process block 2
    tokens = block2.split(' ')
    for key, token in enumerate(tokens):
        if token == 'valid_lft':
            if tokens[key+1] == 'forever':
                data['valid_left'] = -1
            else:
                data['valid_left'] = int(tokens[key+1].strip('sec'))

        if token == 'preferred_lft':
            if tokens[key+1] == 'forever':
                data['preferred_left'] = -1
            else:
                data['preferred_left'] = int(tokens[key+1].strip('sec'))

    return data

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

def get_net_adapter_names(skip_lo=True):
    """Get the names of network adapters"""

    # Iterate over adapter names and skip loopback
    sys_dir = '/sys/class/net'

    if skip_lo:
        interface_names = [iname for iname in os.listdir(sys_dir) if iname != 'lo']
    else:
        interface_names = [iname for iname in os.listdir(sys_dir)]


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
    lines = [line.replace('\n', '') for line in quagga_rt]

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
    cached = False

    # Process the output
    for lineno, line in enumerate(in_lines):
        # Skip headers
        if lineno in [0, 1, 2, 3]:
            continue

        # Process the lines
        # Type Code
        if line[0] == ' ':
            proto = last_proto
            cached = True
        else:
            proto = line[0]

            # Code present, clear cache
            last_proto = proto
            last_subnet = None
            last_ad = None
            last_rd = None
            cached = False

        # Selected
        selected = bool(line[1] == '>')

        # FIB
        fib = bool(line[2] == '*')

        # Handle differently if Routing proto or Directly connected
        tokens = line.split(' ')
        if proto == 'C':
            # Look for anchor 'is'. -1 is subnet, +3 is adapter
            for num, token in enumerate(tokens):
                if token == 'is':
                    subnet = tokens[num-1]
                    last_subnet = subnet
                    adapter = tokens[num+3]
                    ad = None
                    rd = None
                    gw = None
                    break
                else:
                    continue
        else:
            # This is routing protocol line, but it might be directly connected.
            if 'via' in tokens:
                # Look for anchor 'via'.
                for num, token in enumerate(tokens):
                    if token == 'via':
                        if cached:
                            # Load cached
                            subnet = last_subnet
                            ad = last_ad
                            rd = last_rd
                        else:
                            # Parse flieds before 'via'
                            subnet = tokens[num-2]
                            last_subnet = subnet
                            (ad, rd) = tokens[num-1].strip('[]').split('/')
                            ad = int(ad)
                            rd = int(rd)
                            last_ad = ad
                            last_rd = rd

                        gw = tokens[num+1].strip(',')
                        adapter = tokens[num+2].strip(',')
                        break
                    else:
                        continue
            elif 'is' in tokens:
                # Look for anchor 'is'.
                for num, token in enumerate(tokens):
                    if token == 'is':
                        # Extract data
                        subnet = tokens[num-2]
                        last_subnet = subnet
                        (ad, rd) = tokens[num-1].strip('[]').split('/')
                        ad = int(ad)
                        rd = int(rd)
                        last_ad = ad
                        last_rd = rd
                        gw = None
                        adapter = tokens[num+3].strip(',')
                    else:
                        continue
            else:
                raise NotImplementedError

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
