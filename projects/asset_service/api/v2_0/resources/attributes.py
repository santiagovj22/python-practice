# -- attributes.py --

# API endpoints for managing attributes of assets

# EKU Power Drives GmbH 2019, Kristian Binder <kristian.binder@ekupd.com>

# -- external dependencies --
from flask_restplus import Namespace, Resource, fields, abort, inputs, marshal
from flask import current_app as app, request
from flask_restplus.reqparse import RequestParser

from sqlalchemy import exc

# -- project dependencies --
from ..globals.pagination import paginate_with
from ..globals.inactive import inactive_parser
from ..globals.uuid import UUIDField

from models import db
from models.attribute import Attribute, AttributeType


api = Namespace('Attributes', description='attributes of assets')


class AttributeTypeLinks(fields.Raw):
    def __init__(self, **kwargs):
        fields.Raw.__init__(self, **kwargs)
        self.example = self.format('{typename}')
            
    def format(self, typename):
        return {'self': {'href': '/api/v2.0/attributes/types/{}'.format(typename)}} # TODO use url_for


class AttributeLinks(fields.Raw):
    def __init__(self, **kwargs):
        fields.Raw.__init__(self, attribute='asset_uuid_and_typename', **kwargs)
        self.example = self.format(('{asset uuid}', '{attribute typename}'))
            
    def format(self, value):
        uuid, typename = value
        return {'self': {'href': '/api/v2.0/assets/{}/attributes/{}'.format(uuid, typename)}} # TODO use url_for


attribute_get_minimal = api.model('Attribute GET minimal', {
    '_links': AttributeLinks(),
    'typename': fields.String(),
    'value': fields.String(),
})

attribute_type_patch = api.model('AttributeType PATCH', {
    'display_name': fields.String(
        description = 'a human-readable, descriptive name for this attribute type'
    ),
    'description': fields.String(
        description = 'a description of the attribute type'
    ),
    'identifier': fields.Boolean(
        description = 'this attribute type acts as identifier'
    )
})

attribute_type_put = api.inherit('AttributeType PUT', attribute_type_patch, {
    'display_name': fields.String(
        required = True
    ),
    'identifier': fields.Boolean(
        required = True
    )
})

# TODO require typename in attribute_type_put

attribute_type_put_multiple = api.inherit('AttributeType PUT multiple', attribute_type_put, {
    'typename': fields.String(
        description = 'a unique id for this attribute type',
        required = True
    )
})

attribute_type_patch_list = api.model('AttributeType PATCH list', {
    'attribute_types': fields.List(
        fields.Nested(attribute_type_put_multiple),
        description = 'A list of AttributeTypes',
        required = True
    )
})

attribute_type_get = api.inherit('AttributeType GET', attribute_type_patch, {
    '_links': AttributeTypeLinks(
        attribute = 'typename',
    ),
    'typename': fields.String()
})

attribute_patch = api.model('Attribute PATCH', {
    'value': fields.String(),
    'data': fields.Raw(),
})

attribute_post = api.inherit('Attribute POST', attribute_patch, { # api.clone overwrites the cloned model attributes, api.inherit is overwritten by the inherited attributes
    'active': fields.Boolean(
        default = True
    )
})

attribute_put_multiple = api.clone('Attribute PUT multiple', attribute_post, {
    'typename': fields.String(
        required = True
    ),
    'original': UUIDField(
        attribute = 'original.uuid'
    ),
    'asset': UUIDField(
        attribute='asset.uuid',
        required = True
    ),
    'uuid': UUIDField(
        required = True
    ),
    'active': fields.Boolean(
        required = True
    )
})

# TODO use inheritance
attribute_get = api.model('Attribute GET', {
    '_links': AttributeLinks(),
    'uuid': UUIDField(),
    'original': UUIDField(attribute='original.uuid'),
    'typename': fields.String(),
    'asset': UUIDField(attribute='asset.uuid'),
    'value': fields.String(),
    'data': fields.Raw(),
    'active': fields.Boolean(),
    'is_id': fields.Boolean()
})

# attribute_fields = api.model('Attribute', {
#     'uuid': UUIDField(
#         description = 'unique identifier of this attribute value',
#         required = True
#     ),
#     'original': UUIDField(
#         description = 'reference to a disabled previous attribute value that is now replaced by this one'
#     ),
#     'typename': fields.String(
#         description = 'the typename / URN of an attribute',
#         example     = 'equipment:weight',
#         required    = True
#     ),
#     'asset': fields.String(
#         attribute = 'asset_uuid',
#         description = 'reference to the asset this attributes relates to'
#     ),
#     'value': fields.String(
#         description = 'string representation of a simple, unstructured attribute value'
#     ),
#     'data': fields.Raw(
#         description = 'complex data object instead of a simple value'
#     ),
#     'active': fields.Boolean(
#         description = 'indicates whether this attribute is active or it documents an inactive (e.g. old) value',
#         required = True,
#         default = True
#     ),
#     'is_id': fields.Boolean()
# })


@api.route('/states')
@api.hide
class _AttributeStateList(Resource):

    @paginate_with(api,
        embedded_model = attribute_get,
        embedded_key = 'attributes'
    )
    def get(self):
        """Return a list of attribute states.
        For synchronization only."""

        return Attribute.query

    def patch(self):
        """For synchronization only."""

        if not isinstance(request.json, list):
            abort(400, message='Expected list')

        created = 0
        for obj in request.json:
            attribute_put_multiple.validate(obj)
           
            attribute = Attribute.query.get(obj['uuid'])

            if attribute is None:
                attribute = Attribute.create(**obj)
                created += 1
            elif attribute.active and not obj.active:
                attribute.deactivate()

            # TODO detect conflict if an attribute has two replacements from different asset services

        return {
            'changed': len(request.json) - created,
            'created': created
        }
            

@api.route('/types')
class _AttributeTypeList(Resource):

    @paginate_with(api,
        embedded_model = attribute_type_get,
        embedded_key = 'attribute_types'
    )
    def get(self):
        """returns a list of attribute types"""
      
        return AttributeType.query

    @api.hide
    @api.expect(attribute_type_patch_list)
    def patch(self):
        """only use for multiple puts
        For synchronization only."""

        created = 0
        attribute_types = request.json['attribute_types']
        for obj in attribute_types:
            obj = marshal(obj, attribute_type_put_multiple) # this filters out fields not present in the marshalling model
            
            attribute_type = AttributeType.query.get(obj['typename'])

            if attribute_type is None:
                attribute_type = AttributeType.create(**obj)
                created += 1
            else:
                attribute_type.update(**obj)

        return {
            'changed': len(attribute_types) - created,
            'created': created
        }
            

@api.route('/types/<typename>')
class _AttributeType(Resource):

    @api.marshal_with(attribute_type_get)
    def get(self, typename):
        """returns the attribute type"""

        attribute_type = AttributeType.query.get(typename)
        if attribute_type is None:
            abort(404, message='AttributeType {} doesn\'t exist'.format(typename))

        return attribute_type


    @api.expect(attribute_type_put)
    @api.marshal_with(attribute_type_get)
    def put(self, typename):
        """create the attribute type"""
        # body typename will be ignored TODO require body typename to reduce number of necessary models
        if request.json.get('typename') and typename != request.json.get('typename'):
            abort(400, message='typename mismatch in url and json')
        else:
            request.json['typename'] = typename

        try:
            attribute_type = AttributeType.create(**request.json)
        except exc.IntegrityError:
            abort(409, message='AttributeType {} already exists'.format(typename))

        return attribute_type, 201

    @api.expect(attribute_type_patch)
    @api.marshal_with(attribute_type_get)
    def patch(self, typename):
        """update the attribute type"""
        
        try:
            attribute_type = AttributeType.query.get(typename)
        except:
            abort(400, message='AttributeType {} doesn\'t exist'.format(typename))
        
        attribute_type.update(**request.json)
       
        return attribute_type


@api.route('/types/<typename>/distinct_values')
class _AttributeTypeUniqueValues(Resource):

    @api.response(200, 'Success', fields.List(fields.String))
    def get(self, typename):
        """returns the attribute type"""

        attribute_type = AttributeType.query.get(typename)
        if attribute_type is None:
            abort(404, message='AttributeType {} doesn\'t exist'.format(typename))

        res = db.session.query(Attribute.value).filter(Attribute.typename == typename, Attribute.active == True).distinct().all()
        values = [x[0] for x in res]
        return values