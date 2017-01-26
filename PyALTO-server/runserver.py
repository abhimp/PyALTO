"""Main entry file for starting an ALTO server"""

from flask import Flask

from altoserver.upload import netupload
from altoserver.alto import alto
from altoserver import nm

# Buil Flask application
app = Flask(__name__, instance_relative_config=True)

app.register_blueprint(netupload, url_prefix='/upload')
app.register_blueprint(alto, url_prefix='/alto')

# Initialize a simple topology
nm.init_simple_topo()

# Start functioning
if __name__ == '__main__':
    app.run(host='0.0.0.0')
