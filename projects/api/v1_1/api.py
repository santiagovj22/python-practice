# -- api.py --

# this file collects the namespaces of the API and makes them known
# to the application

# EKU Power Drives GmbH 2019, Kristian Binder <kristian.binder@ekupd.com>

# -- external dependencies --
from flask import Blueprint
from flask_restplus import Api

# --project dependencies --
from .resources.datatypes import api as datatypes_ns
from .resources.rows import api as rows_ns
from .resources.sync import api as sync_ns


bp = Blueprint('api_v1_1', __name__)
api = Api(bp,
    version = '1.1',
    title = 'SOPHIA data service',
    description = 'receive, manage, sync and deliver measurement data',
    contact = 'sophia@ekupd.com',
    doc = '/doc',
    validate = True     #enable validation of input data globally for all resources
)


api.add_namespace(datatypes_ns, path='/datatypes')
api.add_namespace(rows_ns, path='/rows')
api.add_namespace(sync_ns, path='/sync')
