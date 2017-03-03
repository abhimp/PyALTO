#!/usr/bin/python

from __future__ import print_function
import os
import json
import re

def get_connections():
    """Build bridged network topology"""
    
    net_topo = {}
    
    bridges = [netname for netname in os.listdir('/sys/devices/virtual/net/') if netname.startswith('b.')]
    for bridge_name in bridges:
        adapters = [adapter.lstrip('lower_') for adapter in os.listdir('/sys/devices/virtual/net/'+bridge_name) if adapter.startswith('lower_')]
        net_topo[bridge_name] = adapters

    return net_topo

def get_names():
    """Extract adapter bindigns from session logs"""
    rundir = None
    adapters = {}

    regex = re.compile('pycore\.[0-9]$')

    for dirname in os.listdir('/tmp'):
        # Scripts have pycore.X while GUI has pycore.XXXX
        if regex.match(dirname):
            rundir = dirname
            break

    if rundir is None:
        print('ERROR: failed to find CORE rundir')
        return

    for fname in os.listdir('/tmp/'+rundir):
        if fname.endswith('.log'):
            with open('/tmp/'+rundir+'/'+fname, 'r') as fp:
                adapters[fname.rstrip('.log')] = parse_node_log(fp)

    return adapters

def parse_node_log(log_stream):
    """Read given log stream and extract all
    virtual adapter data"""

    adapters = []
    parser = NameParserFSM()

    for line in log_stream:
        if parser.feed_line(line):
            adapters.append((parser.glob_name, parser.loc_name))
            parser.reset()

    return adapters

def builddb():
    """Save network topologydb to json"""
    topo = {
        'links': get_connections(),
        'names': get_names()
    }

    with open('/tmp/netdata.json', 'w') as fp:
        fp.write(json.dumps(topo))

class NameParserFSM(object):
    def __init__(self):
        self.state = 'wait'
        self.loc_name = None
        self.glob_name = None

    def feed_line(self, line):
        if self.state == 'wait':
            if line.count('/sbin/ip') == 1:
                self.state = 'ip_cmd'
                return None
        elif self.state == 'ip_cmd':
            if line.count('link') == 1:
                self.state = 'link'
                return None
        elif self.state == 'link':
            if line.count('set') == 1:
                self.state = 'globname'
                return None
        elif self.state == 'globname':
            self.glob_name = line.split("'")[1]
            self.glob_name = self.glob_name.rstrip('p')
            self.state = 'name'
            return None
        elif self.state == 'name':
            if line.count('name') == 1:
                self.state = 'locname'
                return None
        elif self.state == 'locname':
            self.loc_name = line.split("'")[1]
            return True

        # If no fall match - reset
        self.reset()

    def reset(self):
        # Reset
        self.state = 'wait'
        self.loc_name = None
        self.glob_name = None

if __name__ == '__main__':
    builddb()
