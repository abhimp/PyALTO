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
nm.init_simple_topo()
#nm.init_small_topo()

# Start functioning
if __name__ == '__main__':
    app.run(host='0.0.0.0')
