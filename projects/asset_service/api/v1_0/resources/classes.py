# -- classes.py --

# API endpoints for managing asset classes

# EKU Power Drives GmbH 2019, Kristian Binder <kristian.binder@ekupd.com>

# -- external dependencies --
from flask_restplus import Namespace, Resource, fields
from flask import current_app as app

# -- project dependencies --
from ..globals.pagination import pagination_parser
from ..globals.uuid import UUIDField

from models.asset_class import AssetClass,AssetClassMembership


api = Namespace('Classes', description='asset classes')


assetclass_t = api.model('AssetClass', {
    'classname': fields.String(
        description = "URN of the AssetClass",
        required    = True,
        example     = 'eku:sophia:unit:frac-pump'
    ),
    'display_name': fields.String(
        description = "AssetClass Name to show in user interface",
        required    = True,
        example     = 'Frac Pump Unit'
    ),
    'description': fields.String(
        description = ("A more detailed explanationon what this class "
            "represents and where to use it. Might be used in tooltips"),
        required    = True,
        example     = 'Represents High-Pressure pump units used for hydraulic fracturing'
    )
})

assetclassmember_t = api.model('AssetClassMembership', {
    'uuid': UUIDField(
        description = "unique identifier of this attribute value",
        required    = True
    ),
    'asset_uuid': fields.String(
        attribute = "asset_uuid",
        description = "reference to the asset this attributes relates to"
    ),
    'classname': fields.String(
        attribute = "classname",
        description = "name of the class the asset is a member of" 
    )
})


@api.route('/')
class _AssetClassList(Resource):

    @api.expect(pagination_parser)
    @api.marshal_with(assetclass_t)
    def get(self):
        args = pagination_parser.parse_args()

        query = AssetClass.query

        #TODO: query = query.filter....
        assetclass_list = query.paginate(
            args.get('page_no'),
            args.get('page_size') or app.config['pagination']['per_page_default'],
            app.config['pagination']['per_page_max']
        ).items

        return assetclass_list


@api.route('/<classname>')
class _AssetClass(Resource):

    def get(self, classname):
        return {'iam': 'a single assetclass of with name ' + classname}

    @api.expect(assetclass_t)
    def put(self, classname):
        pass

@api.route('/members/')
class _AssetClassMember(Resource):

    @api.marshal_with(assetclassmember_t)
    @api.expect(pagination_parser)
    def get(self):
        args = pagination_parser.parse_args()

        query = AssetClassMembership.query

        #TODO: query = query.filter.....
        assetclassmembership_list = query.paginate(
            args.get('page_no'),
            args.get('page_size') or app.config['pagination']['per_page_default'],
            app.config['pagination']['per_page_max']
        ).items

        return assetclassmembership_list
