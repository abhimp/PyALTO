import json

from flask import Flask, Response

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

    def run(self):
        """Run the web service"""
        self._alto_ws.run()