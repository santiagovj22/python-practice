# -- api.py --

# this file collects the namespaces of the API and makes them known
# to the application

# EKU Power Drives GmbH 2019, Kristian Binder <kristian.binder@ekupd.com>

# -- external dependencies --
from flask import Blueprint
from flask_restplus import Api

# --project dependencies --
from .resources.assets import api as assets_ns
from .resources.attributes import api as attributes_ns
from .resources.relations import api as relations_ns
from .resources.classes import api as classes_ns
from .resources.identifiers import api as identifiers_ns
from .resources.activity import api as activity_ns


bp = Blueprint('api1_0', __name__, url_prefix='/api/v1.0')
api = Api(bp,
    version = '1.0',
    title = 'SOPHIA asset service',
    description = 'receive, manage and provide information about assets and their relations',
    contact = 'sophia@ekupd.com',
    doc = '/doc',
    validate = True     #enable validation of input data globally for all resources
)


api.add_namespace(assets_ns, path='/assets')
api.add_namespace(attributes_ns, path='/attributes')
api.add_namespace(relations_ns, path='/relations')
api.add_namespace(classes_ns, path='/classes')
api.add_namespace(identifiers_ns, path='/identifiers')
api.add_namespace(activity_ns, path='/activity')
