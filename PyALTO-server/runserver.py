"""Main entry file for starting an ALTO server"""
import logging

from flask import Flask

from altoserver.upload import netupload
from altoserver.alto import alto
from altoserver import nm

# Set logging params
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(asctime)s %(message)s')

# Buil Flask application
app = Flask(__name__, instance_relative_config=True)

app.register_blueprint(netupload, url_prefix='/upload')
app.register_blueprint(alto, url_prefix='/alto')

# Initialize a simple topology
#nm.init_simple_topo()
nm.init_small_topo()

# Start functioning
if __name__ == '__main__':
    app.run(host='0.0.0.0')
