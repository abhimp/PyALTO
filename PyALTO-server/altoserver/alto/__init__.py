"""
ALTO protocol RESTful API.
Functions here should be only a shim between Flask and ALTO
implementation in AltoServer class
"""
import json
import logging

from flask import Blueprint, Response, request, abort

from altoserver.alto.altoserver import AltoServer

alto_server = AltoServer()
alto = Blueprint('alto', __name__)

@alto.route('/networkmap')
def get_network_map():
    """Get ALTO network map """ 

    # TODO: Any request validity checking here

    # Get the map
    try:
        resp = alto_server.get_network_map()
    except Exception as exc:
        logging.exception('Exc in networkmap', exc_info = exc)
        abort(500)
        
    # Return properly structured response
    return Response(
        json.dumps(resp),
        mimetype='application/alto-networkmap+json'
    )

@alto.route('/endpointprop/lookup', methods=['POST'])
def get_endpoint_properties():
    """Return endpoint properties [RFC7285] p 11.4.1"""

    # Do any other request checks

    # Drop early if not json
    if not request.is_json:
        abort(400)

    req_data = request.json

    # Ensure that required keys are there
    if 'properties' not in req_data:
        abort(400)

    if 'endpoints' not in req_data:
        abort(400)

    # Request data. Do not try to parse requested
    # data here. This is only a shim layer
    try:
        resp = alto_server.get_endpoint_properties(
            req_data['properties'],
            req_data['endpoints']
        )
    except Exception as exc:
        logging.exception('Exc in endpoint properties', exc_info = exc)
        abort(500)

    # Return if successfull
    return Response(
        json.dumps(resp),
        mimetype='application/alto-endpointprop+json'
    )

@alto.route('/endpointcost/lookup', methods=['POST'])
def get_endpoint_cost():
    """Return endpoint costs [RFC7285] p 11.5.1"""
    # Do any other request checks

    # Drop early if not json
    if not request.is_json:
        abort(400)

    req_data = request.json

    # Ensure that required keys and data are there
    if 'cost-type' not in req_data:
        abort(400)

    if 'cost-mode' not in req_data['cost-type']:
        abort(400)

    if 'cost-metric' not in req_data['cost-type']:
        abort(400)

    if 'endpoints' not in req_data:
        abort(400)

    if 'srcs' not in req_data['endpoints']:
        abort(400)

    if 'dsts' not in req_data['endpoints']:
        abort(400)

    if not any(req_data['endpoints']['srcs']):
        abort(400)

    if not any(req_data['endpoints']['dsts']):
        abort(400)

    # Request data. Do not try to parse requested
    # data here. This is only a shim layer

    try:
        resp = alto_server.get_endpoint_costs(
            req_data['cost-type'],
            req_data['endpoints']
        )
    except Exception as exc:
        logging.exception('Exc in endpoint costs', exc_info = exc)
        abort(500)

    # Return if successfull
    return Response(
        json.dumps(resp),
        mimetype='application/alto-endpointcost+json'
    )
