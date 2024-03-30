# -- assets.py --

# API functions to manage assets

# EKU Power Drives GmbH 2019, Kristian Binder <kristian.binder@ekupd.com>

# -- external dependencies --
from flask_restplus import Namespace, Resource, fields, marshal_with, inputs, marshal, abort
from flask_restplus.reqparse import RequestParser
from flask import current_app as app, request
from uuid import UUID
from sqlalchemy import or_, exc
import logging

# -- project dependencies --
from ..globals.pagination import paginate_with
from ..globals.inactive import inactive_parser
from ..globals.uuid import UUIDField

from models.asset import Asset
from models.asset_class import AssetClass
from models.identifier import Identifier
from models.attribute import Attribute, AttributeType
from models.relation import Relation
from .classes import class_get_minimal, _AssetClassMemberList


api = Namespace('Assets', description='actual assets')

class AssetLinks(fields.Raw):
    def __init__(self, **kwargs):
        fields.Raw.__init__(self, attribute='uuid', **kwargs)
        self.example = self.format('{identifier}')
    
    def format(self, uuid):
        # return {'self': {'href': url_for('test1', identidier=uuid)}} # TODO use url_for
        return {'self': {'href': '/api/v2.0/assets/{}'.format(uuid)}}

# minimal models have to be defined prior to impoting other modules because they might require these minimal model
asset_get_minimal = api.model('Asset GET minimal', {
    '_links': AssetLinks(),
    'uuid': UUIDField(
        description = 'The Asset\'s unique identifier as a UUID.v4 string'
    ),
    'title': fields.String(), # TODO description string
    'classes': fields.List(
        fields.Nested(class_get_minimal),
        description = 'The Asset\'s classes list'
    )
})

from .relations import relation_get, relation_get_minimal_inbound, relation_get_minimal_outbound, _RelationList
from .attributes import attribute_get, attribute_post, attribute_patch, attribute_get_minimal # paginate_attribute_states

asset_patch = api.model('Asset PATCH', {
    'title': fields.String(
        description = 'a human-readable, descriptive Name for this asset',
        example = 'Pump #939871'
    ),
    'summary': fields.String(
        description = 'optional: additional information on this asset or its purpose'
    )
})

asset_post = api.inherit('Asset POST', asset_patch, {
    'title': fields.String(
        required = True
    )
})

asset_put = api.inherit('Asset PUT', asset_post, {
    'uuid': UUIDField(
        description = 'The Asset\'s unique identifier as a UUID.v4 string',
        required = True
    )
})

asset_patch_list = api.model('Asset PATCH list', {
    'assets': fields.List(
        fields.Nested(asset_put)
    )
})

asset_get = api.clone('Asset GET', asset_patch, { # TODO why clone here?
    '_links': AssetLinks(),
    'uuid': UUIDField(
        description = 'The Asset\'s unique identifier as a UUID.v4 string'
    ),
    'identifiers': fields.List(
        fields.Nested(attribute_get_minimal)
    ),
    'attributes': fields.List(
        fields.Nested(attribute_get_minimal),
        description = 'attributes linked to this asset',
        attribute = 'attributes_active'
    ),
    'classes': fields.List(
        fields.Nested(class_get_minimal)
    ),
    'relations_inbound': fields.List(
        fields.Nested(relation_get_minimal_inbound),
        attribute = 'relations_inbound_active'
    ),
    'relations_outbound': fields.List(
        fields.Nested(relation_get_minimal_outbound),
        attribute = 'relations_outbound_active'
    )
})

assetlist_parser = RequestParser()
assetlist_parser.add_argument('classes_and',
    location='args',
    action='split',
    help='list assets matching all of the given classnames (comma-separated)'
)
assetlist_parser.add_argument('classes_or',
    location='args',
    action='split',
    help='list assets matching any of the given classnames (comma-separated)'
)
assetlist_parser.add_argument('related_class',
    location='args',
    help='list assets related to an asset of the given class'
)
assetlist_parser.add_argument('attribute',
    location='args',
    help="list assets having the given attribute assigned"
)
assetlist_parser.add_argument('value',
    location='args',
    help="list assets matching the attribute value"
)
assetlist_parser.add_argument('value_contains',
    location='args',
    help="list assets matching the attribute value partially"
)
assetlist_parser.add_argument('title_contains',
    location='args',
    help="filter asset title to match search string"
)
assetlist_parser.add_argument('expand',
    type = inputs.boolean,
    default = False,
    help = 'show all hidden fields'
)


@api.route('/')
class _AssetList(Resource):

    @paginate_with(api,
        embedded_model = asset_get,
        embedded_key = 'assets',
        embedded_mask = '{_links, title}' # sets the default value for X-Fields, all fields are documented
    )
    @api.expect(assetlist_parser)
    def get(self):
        """return a list of assets.
        The amount of details returned for each asset can be controlled with parameters.
        Please note:
         * Only one of the parameters 'class_and' and 'class_or' can be specified in a request!
         * Only one of the parameters 'value' and 'value_contains' can be specified in a request! The 'attribute' parameter must be given!

        """

        args = assetlist_parser.parse_args()
        try:
            return Asset.listquery(filters=args)
        except Exception as e:
            abort(400, message=e)


    @api.expect(asset_post)
    @api.marshal_with(asset_get)
    @api.response(409, 'Duplicate identifier')
    @api.response(422, 'Unknow class')
    def post(self):
        """append an Asset to the List"""

        try:
            asset = Asset.create(**request.json)
            return asset, 201
        except exc.IntegrityError as e:
            msg = str(e).split('\n')[1].lstrip('DETAIL:  ')
            abort(400, message=msg)
        except Exception as e:
            abort(400, message=e)

    @api.hide
    @api.expect(asset_patch_list)
    def patch(self):
        """multiple puts"""

        created = 0
        assets = request.json['assets']
        for obj in assets:

            obj = marshal(obj, asset_put)
            
            asset = Asset.query.get(obj['uuid'])
            if asset is None:
                asset = Asset.create(**obj)
                created += 1
            else:
                asset.update(**obj)

        return {
            'changed': len(assets) - created,
            'created': created
        }


@api.route('/<identifier>', endpoint='test1') # endpoint for fields.Url
@api.param('identifier', description='UUID or one of the alternative identifiers of the asset', _in='query')
class _Asset(Resource):

    @api.marshal_with(asset_get) # mask='{title}'
    @api.response(404, 'Asset not found')
    def get(self, identifier):
        """returns the asset that matches the identifier"""
        return asset_by_id_or_abort(identifier)

    @api.expect(asset_patch)
    @api.marshal_with(asset_get)
    @api.response(404, 'Asset not found')
    def patch(self, identifier):
        """update the asset that matches the identifier"""
        # only title and description
        asset = asset_by_id_or_abort(identifier) # TODO implement something like get_or_404 on model layer
        obj = marshal(request.json, asset_patch, skip_none=True)
        asset.update(**obj)
        return asset


@api.route('/<identifier>/attributes')
class _AssetAttributeList(Resource):

    @paginate_with(api,
        embedded_model = attribute_get,
        embedded_key = 'attributes'
    )
    @api.response(404, 'Asset not found') # always put befor paginate decorator
    def get(self, identifier):
        """returns a list of attributes for this asset"""
        
        asset = asset_by_id_or_abort(identifier)
        return asset.query_attributes()


@api.route('/<identifier>/attributes/<typename>')
class _AssetAttribute(Resource):

    @api.marshal_with(attribute_get)
    @api.response(404, 'Asset or attribute not found')
    def get(self, identifier, typename):
        """returns the attribute of the specified type for this asset"""

        asset = asset_by_id_or_abort(identifier)
        attribute = asset_attribute_or_abort(asset, typename)
        return attribute

    
    @api.expect(attribute_post)
    @api.marshal_with(attribute_get)
    @api.response(404, 'Asset or AttributeType not found')
    @api.response(409, 'Asset already has an attribute of this type')
    def post(self, identifier, typename):
        """create the attribute of the specified type for this asset"""

        asset = asset_by_id_or_abort(identifier)

        try:
            AttributeType.query.get(typename)
        except:
            abort(404, message='Attribute type doesn\'t exist')

        if typename in asset.attributes_dict.keys():
            abort(409, message='Asset already has an attribute of this type')

        obj = marshal(request.json, attribute_post, skip_none=True)

        attribute = Attribute.create(asset=asset, typename=typename, **obj)
       
        return attribute, 201


    @api.expect(attribute_patch)
    @api.marshal_with(attribute_get)
    @api.response(404, 'Asset or AttributeType not found')
    def patch(self, identifier, typename):
        """update the attribute of the specified type for this asset"""

        asset = asset_by_id_or_abort(identifier)
        attribute = asset_attribute_or_abort(asset, typename)
        obj = marshal(request.json, attribute_patch, skip_none=True)
        attribute = attribute.update(**obj)

        return attribute, 200


    def delete(self, identifier, typename):
        """delete the attribute of the specified type for this asset"""

        asset = asset_by_id_or_abort(identifier)
        attribute = asset_attribute_or_abort(asset, typename)
        attribute.deactivate()

        return 'deleted', 200


@api.route('/<identifier>/relations')
@api.param('identifier', description='UUID or one of the alternative identifiers of the asset')
class _AssetRelations(_RelationList):

    # TODO remove this, inheridted get method uses identifier parameter
    # @api.response(404, 'Asset not found')
    # def get(self, identifier):
    #     """same output as /relations"""
    #     asset = asset_by_id_or_abort(identifier)
    #     return super().get(asset=asset)

    # TODO post() is otherwiese inherited
    @api.hide
    def post(self, identidier):
        pass
        
@api.route('/<identifier>/relations/<typename>')
@api.param('identifier', description='UUID or one of the alternative identifiers of the asset')
@api.param('typename', description='name of the relation type')
class _AssetRelation(Resource):

    @api.marshal_with(relation_get)
    def get(self, identifier, typename):
        pass
        asset = asset_by_id_or_abort(identifier)
        relation = Relation.query.filter(
            or_(
                Relation.asset_dst_uuid == asset.uuid,
                Relation.asset_src_uuid == asset.uuid
            )
        ).filter(Relation.typename == typename).one_or_none()

        if relation is None:
            abort(404, message='Asset has no relation of this type')

        return relation


@api.route('/<identifier>/classes')
class _AssetClassList(_AssetClassMemberList):
    pass

        

def asset_by_id_or_abort(identifier):
    asset = Asset.from_id(identifier)
    if asset is None:
        abort(404, message='No asset for this identifier')
    return asset

def asset_attribute_or_abort(asset, typename):
    try:
        return asset.attributes_dict[typename]
    except:
        abort(404, message='Asset has no attribute of this type')