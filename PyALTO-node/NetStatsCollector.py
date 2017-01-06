import os
import ipaddress
import logging

class NetStatsCollector(object):
    """
    A class used to collect network parameters of the virtual device
    the collector is running on. Collected data is periodically
    delivered to the central device for further processing.
    """
    def __init__(self):
        """Instantiate the stats collector"""
        pass

    def collect_all_interface_stats(self):
        """Collect and return stats of all interfaces"""
        pass

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
            with open(stat_path, 'r') as fp:
                stat_data['stats'][stat] = int(fp.read())

        # Return the collected data
        return stat_data



