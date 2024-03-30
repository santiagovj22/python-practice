# -- rows.py --

# API functions to manage data rows

# EKU Power Drives GmbH 2019, Kristian Binder <kristian.binder@ekupd.com>

# -- external dependencies --
from flask_restplus import Namespace, Resource, fields, abort
from flask import current_app as app, request
from uuid import UUID
import sqlalchemy.exc
import psycopg2.errors


# -- project dependencies --
from ..globals.pagination import pagination_parser
from ..globals.uuid import UUIDField
from .datatypes import typename_t
from models.row import Row
from models.meta_source import MetaSource




api = Namespace('Sources', description='manage sources')


source = api.model('source', {
    'id': fields.Integer( description = 'Database identifier for source'),
    'source': fields.Raw( description = 'Source as a JSON object')
})
source_put = api.model('Source PUT',{
    'source': fields.Raw( description = 'Source as a JSON object')
})

@api.route('/')
class Sources(Resource):
    @api.marshal_with(source) 
    def get(self):
        ''' Returns all available sources '''
        #sources = MetaSource.getSourceIdFromFatnodeUUID(args['source_uuid']).all()
        return MetaSource.query.all() 

@api.route('/<string:fatnode_uuid>')
#@api.param('identifier', description='UUID or one of the alternative identifiers of the asset', _in='query')
class Sources(Resource):
    
    @api.marshal_with(source) 
    def get(self,fatnode_uuid):
        ''' Returns all available sources from given fatnode '''
        #sources = MetaSource.getSourceIdFromFatnodeUUID(args['source_uuid']).all()
        return MetaSource.getSourceIdFromFatnodeUUID(fatnode_uuid).all()

    @api.expect(source_put)
    @api.marshal_with(source) 
    @api.response(409, 'Source with same fatnode uuid already exists')
    def put(self,fatnode_uuid):
        ''' Creates a new source entry based on fatnode uuid '''
        #sources = MetaSource.getSourceIdFromFatnodeUUID(args['source_uuid']).all()

        result = MetaSource.getSourceIdFromFatnodeUUID(fatnode_uuid).one_or_none()
        if result is not None:
            abort(409, message='Source with same fatnode uuid already exists')

        newsource = MetaSource.create()
        print('##########################',result)
        return newsource, 201

