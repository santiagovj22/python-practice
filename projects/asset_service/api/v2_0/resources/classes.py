# -- classes.py --

# API endpoints for managing asset classes

# EKU Power Drives GmbH 2019, Kristian Binder <kristian.binder@ekupd.com>

# -- external dependencies --
from flask_restplus import Namespace, Resource, fields, marshal, abort
from flask import current_app as app, request

from sqlalchemy import exc

# -- project dependencies --
from ..globals.pagination import paginate_with
from ..globals.uuid import UUIDField

from models.asset_class import AssetClass, AssetClassMembership
from models.asset import Asset


api = Namespace('Classes', description='asset classes')

class ClassLinks(fields.Raw):
    def __init__(self, **kwargs):
        fields.Raw.__init__(self, attribute='classname', **kwargs)
        self.example = self.format('{class_name}')
            
    def format(self, class_name):
        return {'self': {'href': '/api/v2.0/classes/{}'.format(class_name)}}

class ClassMembershipLinks(fields.Raw):
    def __init__(self, **kwargs):
        fields.Raw.__init__(self, attribute='uuid', **kwargs)
        self.example = self.format('{uuid}')
            
    def format(self, uuid):
        return {'self': {'href': '/api/v2.0/classes/members/{}'.format(uuid)}}


assetclass_patch = api.model('AssetClass PATCH', {
    'display_name': fields.String(),
    'description': fields.String(
        description = 'URN of the AssetClass',
        example = 'eku:sophia:unit:frac-pump'
    )
})

assetclass_put = api.inherit('AssetClass PUT', assetclass_patch, {
    'classname': fields.String(
        required = True
    ),
    'display_name': fields.String(
        required = True
    ),
    'description': fields.String(
        required = True
    )
})

asset_class_get = api.model('AssetClass GET', {
    '_links': ClassLinks(),
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

class_get_minimal = api.model('Class GET minimal', {
    '_links': ClassLinks(),
    'classname': fields.String(
        description = 'URN of the AssetClass',
        example = 'eku:sophia:unit:frac-pump'
    )
})

asset_class_membership_post = api.model('AssetClassMembership POST', {
    'asset_uuid': fields.String(
        description = 'reference to the asset',
        required = True
    ),
    'classname': fields.String(
        description = 'name of the class the asset is a member of',
        required = True
    )
})

asset_class_membership_get = api.inherit('AssetClassMembership GET', asset_class_membership_post, {
    '_links': ClassMembershipLinks(),
    'uuid': UUIDField(
        description = 'unique identifier of this class membership',
        required = True
    )
})


@api.route('/')
class _AssetClassList(Resource):

    @paginate_with(api,
        embedded_model = asset_class_get,
        embedded_key = 'asset_classes'
    )
    def get(self):
        #TODO: query = query.filter....
        return AssetClass.query


@api.route('/<classname>')
class _AssetClass(Resource):

    @api.marshal_with(asset_class_get)
    def get(self, classname):
        asset_class = AssetClass.query.get(classname)
        if asset_class is None:
            abort(404, message='AssetClass {} doesn\'t exist'.format(classname))

        return asset_class


    @api.expect(assetclass_patch)
    @api.marshal_with(asset_class_get)
    def patch(self, classname):
        asset_class = AssetClass.query.get(classname)
        if asset_class is None:
            abort(404, message='AssetClass {} doesn\'t exist'.format(classname))

        obj = marshal(request.json, assetclass_patch, skip_none=True)
        
        asset_class.update(**obj)

        return asset_class


    @api.expect(assetclass_put)
    @api.marshal_with(asset_class_get)
    def put(self, classname):
        
        if request.json['classname'] != classname:
            abort(400, message='classname mismatch in url and json')

        obj = marshal(request.json, assetclass_put)
        
        try:
            asset_class = AssetClass.create(**obj)
        except exc.IntegrityError:
            abort(409, message='AssetClass {} already exists'.format(classname))

        return asset_class, 201

@api.route('/members/')
class _AssetClassMemberList(Resource):

    @paginate_with(api,
        embedded_model = asset_class_membership_get,
        embedded_key = 'asset_class_members'
    )
    def get(self, identifier=None):
        query = AssetClassMembership.query

        if identifier is not None:
            asset = Asset.from_id(identifier)
            if asset is None:
                abort(404, message='No asset for this identifier')
            else:
                query = query.filter(AssetClassMembership.asset_uuid == asset.uuid)

        #TODO: query = query.filter.....
        return query

    @api.expect(asset_class_membership_post)
    @api.marshal_with(asset_class_membership_get)
    def post(self):
        """create a membership relation for an asset in a class"""

        try:
            membership = AssetClassMembership.create(**request.json)
            return membership, 201
        except exc.IntegrityError as e:
            msg = str(e).split('\n')[1].lstrip('DETAIL:  ')
            abort(400, message=msg)
        except Exception as e:
            abort(400, message=e)
        

@api.route('/members/<uuid>')
class _AssetClassMembership(Resource):

    @api.marshal_with(asset_class_membership_get)
    # @api.param('uuid', description='the memberships UUID', _in='query')
    def get(self, uuid):
        """returns a class membership"""
        membership = AssetClassMembership.query.get(uuid)
        return membership


    

    