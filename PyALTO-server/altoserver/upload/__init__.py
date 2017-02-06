"""
Flask blueprint implementing RESTful web interface
used to upload various network parameters.
"""
import logging
import json

from flask import Blueprint, request, Response, abort
from altoserver import nm

netupload = Blueprint('netupload', __name__)

@netupload.route('/<device_name>/adapter_addr', methods=['GET', 'POST'])
def upload_device_adapter_addr(device_name):
    """Process the incomming request with adapter(s) addresses"""

    # Process GET for easier debugging
    if request.method == 'GET':
        # Return error response
        resp = Response(
            response=json.dumps({'error':'GET not allowed'}),
            mimetype='application/json'
        )
        resp.status_code = 405
        return resp

    if not request.is_json:
        abort(400)

    # Check if we have a node with given name
    node = nm.get_device_by_name(device_name)
    if node is None:
        abort(400)

    # Merge all addresses of all adapters
    addresses = []
    for lines in request.json.values():
        addresses.extend(lines)

    node.update_interface_addresses(addresses)

    # Processed fine
    return ('', 204)

@netupload.route('/<device_name>/adapter_stats', methods=['GET', 'POST'])
def upload_device_adapter_stats(device_name):
    """Process the incomming request with adapter stats"""

    # Process GET for easier debugging
    if request.method == 'GET':
        # Return error response
        resp = Response(
            response=json.dumps({'error':'GET not allowed'}),
            mimetype='application/json'
        )
        resp.status_code = 405
        return resp

    if not request.is_json:
        abort(400)

    # Check if we have a node with given name
    node = nm.get_device_by_name(device_name)
    if node is None:
        abort(400)

    # Add stats to stats deque
    node.update_adapter_stats(request.json)

    # Processed fine
    return ('', 204)

@netupload.route('/<device_name>/rtable', methods=['GET', 'POST'])
def upload_device_routing_table(device_name):
    """Process the incomming request with routing table data"""

    # Process GET for easier debugging
    if request.method == 'GET':
        # Return error response
        resp = Response(
            response=json.dumps({'error':'GET not allowed'}),
            mimetype='application/json'
        )
        resp.status_code = 405
        return resp

    # Process post request
    if not request.is_json:
        abort(400)

    # Check if we have a node with given name
    node = nm.get_device_by_name(device_name)
    if node is None:
        abort(400)

    # Add stats to stats deque
    node.update_routing_table(request.json)

    # Processed fine
    return ('', 204)

@netupload.route('/<device_name>/quagga_rt', methods=['GET', 'POST'])
def upload_quagga_routing_table(device_name):
    """Process the incomming request with quagga routing table"""

    # Process GET for easier debugging
    if request.method == 'GET':
        # Return error response
        resp = Response(
            response=json.dumps({'error':'GET not allowed'}),
            mimetype='application/json'
        )
        resp.status_code = 405
        return resp

    if not request.is_json:
        abort(400)

    # Check if we have a node with given name
    node = nm.get_device_by_name(device_name)
    if node is None:
        abort(400)

    # Add stats to stats deque
    node.update_quagga_routing_table(request.json)

    # Processed fine
    return ('', 204)
