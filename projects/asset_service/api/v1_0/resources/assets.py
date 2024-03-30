# -- assets.py --

# API functions to manage assets

# EKU Power Drives GmbH 2019, Kristian Binder <kristian.binder@ekupd.com>

# -- external dependencies --
from flask_restplus import Namespace, Resource, fields, marshal_with, inputs, marshal, abort
from flask_restplus.reqparse import RequestParser
from flask import current_app as app, request
from uuid import UUID
from functools import wraps
from sqlalchemy.orm import exc
import logging

# -- project dependencies --
from ..globals.pagination import pagination_parser
from ..globals.inactive import inactive_parser
from ..globals.uuid import UUIDField
from .identifiers import identifier_t, idtypename_t, idtype_t, IdentifierListToDictMapper
from .classes import assetclass_t
from .attributes import attribute_t
from .relations import relation_t, _RelationList

from models.asset import Asset
from models.asset_class import AssetClass
from models.identifier import Identifier
from models.attribute import Attribute

api = Namespace('Assets', description='actual assets')

asset_t_base = api.model('Asset_base', {
    'uuid': UUIDField(
        description = "The Asset's unique identifier as a UUID.v4 string"
    ),
    'title': fields.String(
        description = "a human-readable, descriptive Name for this asset",
        required    = True,
        example     = 'Pump #939871'
    ),
    'summary': fields.String(
        description = "optional: additional information on this asset or its purpose",
    ),
    'identifiers': fields.Raw(
        description = "List of additional identifiers for this asset to reference it",
        mask = IdentifierListToDictMapper
    ),
    'classes': fields.List(
        fields.String(
            attribute   = 'classname',
            description = "a class name",
            example     = 'eku:sophia:ding'
        ),
        description = "List of classes this asset is assigned to",
        default     = [],
    )
})

asset_t_full = api.inherit('Asset_full', asset_t_base, {
    'creation_date': fields.DateTime(
        description = "date and time of asset object creation as ISO8601 string",
        dt_format   = 'iso8601',
        example     = '2019-01-01T01:00:00Z'
    ),
    'creation_user': fields.String(),
    'attributes': fields.List(
        fields.Nested(attribute_t),
        attribute='attributes_active',
        description = "attributes linked to this asset"
    ),
    'relations_inbound': fields.List(
        fields.Nested(relation_t),
        attribute='relations_inbound_active'
    ),
    'relations_outbound': fields.List(
        fields.Nested(relation_t),
        attribute='relations_outbound_active'
    )
})


#TODO: try to use "Marshmallow" to parse request arguments because of reqparse being marked deprecated
# https://flask-restplus.readthedocs.io/en/stable/parsing.html
assetlist_parser = RequestParser()
assetlist_parser.add_argument('class',
    location='args',
    help="list assets of the given class"
)
assetlist_parser.add_argument('class-all',
    location='args',
    action='split',
    help="list assets matching all of the given classnames (comma-separated)"
)
assetlist_parser.add_argument('class-oneof',
    location='args',
    action='split',
    help="list assets matching one of the given classnames (comma-separated)"
)
assetlist_parser.add_argument('attribute',
    location='args',
    help="list assets having the given attribute assigned"
)
assetlist_parser.add_argument('value',
    location='args',
    help="list assets matching the attribute value"
)
assetlist_parser.add_argument('value-like',
    location='args',
    help="list assets matching the attribute value partially"
)
assetlist_parser.add_argument('title-like',
    location='args',
    help="filter asset title to match search string"
)
assetlist_parser.add_argument('expand',
    type = inputs.boolean,
    default = False,
    help = 'list attributes of the given assets'
)

# TODO try to get errors documented automatically
# class NoAttributeException(Exception):
#     message = 'attribute needed for value'

# @api.errorhandler(NoAttributeException)
# def handle_no_attribute_Exception(error):
#     return {'message': error.message}, 400

def selective_marshal_with(asset_t_base,asset_t_full):
    """
    Selective response marshalling. Doesn't update apidoc.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if assetlist_parser.parse_args()['expand']:
                model = asset_t_full
            else:
                model = asset_t_base

            func2 = marshal_with(model, skip_none=True)(func)
            return func2(*args, **kwargs)
        return wrapper
    return decorator

@api.route('/')
class _AssetList(Resource):

    @api.expect(assetlist_parser)
    @api.expect(pagination_parser)
    @api.expect(inactive_parser)
    @selective_marshal_with(asset_t_base, asset_t_full)
    @api.doc(model=asset_t_base)
    # @api.marshal_with(asset_t_base)
    # @api.response(400, 'test error')

    def get(self):
        """return a list of assets.
        The amount of details returned for each asset can be controlled with parameters.
        Please note:
         * Only one of the parameters 'class', 'class-all' and 'class-oneof' can be specified in a request!
         * Only one of the parameters 'value' and 'value-like' can be specified in a request! The 'attribute parameter must be given!

        :raises NoAttributeException: In case of something
        """

        args = assetlist_parser.parse_args()
        args.update(pagination_parser.parse_args())
        args.update(inactive_parser.parse_args())

        # --- asset filters changed ---
        if args.get('class') is not None:
            args['classes_and'] = [args.get('class')]
        elif args.get('class-all') is not None:
            args['classes_and'] = args.get('class-all')
        elif args.get('class-oneof') is not None:
            args['classes_or'] = args.get('class-oneof')
        # --- END ---

        if args['attribute'] is None and any([args[param] is not None for param in ['value', 'value-like']]):
            abort(400, message='attribute needed for value')
            # raise NoAttributeException

        if all([args[param] is not None for param in ['value', 'value-like']]):
            abort(400, message='can\'t combine parameters value and value-like')

        query = Asset.listquery(filters=args)

        if args.get('show_inactive') is not True:
            query.filter(Attribute.active == True)

        assets_list = query.paginate(
            args.get('page_no'),
            args.get('page_size') or app.config['pagination']['per_page_default'],
            app.config['pagination']['per_page_max']
        ).items

        return assets_list

    @api.expect(asset_t_base)
    @api.marshal_with(asset_t_base)
    def post(self):
        """append an Asset to the List"""
        
        asset = Asset.create(**request.json)
        return asset


@api.route('/<identifier>')
@api.param('identifier', description='UUID or one of the alternative identifiers of the asset', _in='query')
class _Asset(Resource):

    @api.marshal_with(asset_t_full)
    def get(self, identifier):

        try:
            return Asset.from_id(identifier)

        except exc.NoResultFound as e:
            msg = 'No asset found matching given identifier "{i}"'.format(i=identifier)
            logging.warning(msg)
            abort(404, msg)

        except Exception as e:
            msg = 'other error on asset lookup: {e}'.format(e=str(e))
            logging.warning(msg)
            abort(500, msg)
    
    def put(self, identifier, data):
        pass

#TODO: find out how to do that...
#api.add_resource(_RelationList, '/<identifier>/relations')


@api.route('/<identifier>/relations')
@api.param('identifier', description='UUID or one of the alternative identifiers of the asset', _in='query')
class _AssetRelations(_RelationList):

    def get(self, identifier):
        try:
            return super().get(asset_id = identifier)

        except exc.NoResultFound as e:
            msg = 'No asset relations found matching given identifier "{i}"'.format(i=identifier)
            logging.warning(msg)
            abort(404, msg)

        except Exception as e:
            msg = 'other error on asset relations lookup: {e}'.format(e=str(e))
            logging.warning(msg)
            abort(500, msg)
