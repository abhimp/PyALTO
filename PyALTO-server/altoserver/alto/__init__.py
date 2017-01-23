"""
ALTO protocol implementation (RESTful API)
"""
import json
import logging

from flask import Blueprint, Response, request, abort

from altoserver.networkmap import AltoPID
from altoserver import nm

alto = Blueprint('alto', __name__)

@alto.route('/networkmap')
def get_network_map():
    """Return ALTO network map per [RFC7285] p11.2.1""" 

    # Get internal network representation
    (meta, map) = nm.get_pid_topology()

    # Add pids
    nmap = {}
    for pid in map:
        (name, data) = pid.get_json_repr()
        nmap[name] = data
    
    # Build the response
    resp = {
        'meta': meta,
        'network-map': nmap
    }

    return Response(
        json.dumps(resp),
        mimetype='application/alto-networkmap+json'
    )

@alto.route('/endpointprop/lookup', methods=['POST'])
def get_endpoint_properties():
    """Return endpoint properties [RFC7285] p 11.4.1"""

    # Ignore requested properties
    # The only mandatory requirement is PID lookup (p 11.4.1.4)

    # Drop early if not json
    if not request.is_json:
        abort(400)

    req_data = request.json

    print(req_data)

    # Validate properties

    # Request data

    # Format and return the response
    response = {'status': 'OK'}

    return Response(
        json.dumps(response),
        mimetype='application/alto-endpointprop+json'
    )
                   