import json

from flask import Flask, Response, abort

class AltoWebService(object):
    """Class implementing ALTO server WEB access"""

    def __init__(self, als):
        """Initialize the server"""
        self._alto_ws = Flask(__name__)
        self._als = als
        
        @self._alto_ws.route("/")
        def home_page():
            return "ALTO SERVER"

        @self._alto_ws.route("/networkmap")
        def network_map():
            nm = self._als.get_network_map()
            return Response(
                json.dumps(nm), 
                mimetype="application/alto-networkmap+json")

        @self._alto_ws.route("/costmap/<mode>/<metric>")
        def cost_map(mode, metric):
            # Ensure basic correctness of the request
            if mode != "numerical" and mode != "ordinal":
                abort(400)
            if metric != "routingcost":
                abort(400)

            # Get and return the costmap
            cm = self._als.get_cost_map(mode, metric)
            return Response(
                json.dumps(cm),
                mimetype="application/alto-costmap+json")

    def run(self):
        """Run the web service"""
        self._alto_ws.run()