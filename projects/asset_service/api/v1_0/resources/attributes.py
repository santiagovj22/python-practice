# -- attributes.py --

# API endpoints for managing attributes of assets

# EKU Power Drives GmbH 2019, Kristian Binder <kristian.binder@ekupd.com>

# -- external dependencies --
from flask_restplus import Namespace, Resource, fields
from flask import current_app as app

# -- project dependencies --
from ..globals.pagination import pagination_parser
from ..globals.inactive import inactive_parser
from ..globals.uuid import UUIDField

from models.attribute import Attribute, AttributeType


api = Namespace('Attributes', description='attributes of assets')


attributetypename_t = fields.String(
    description = "the typename / URN of an attribute",
    example     = 'equipment:weight',
    required    = True
)

attributetype_t = api.model('AttributeType', {
    'typename': attributetypename_t,
    'display_name': fields.String(),
    'description': fields.String(),
    'unique': fields.Boolean(),
    'identifier': fields.Boolean()
})

attribute_t = api.model('Attribute', {
    'uuid': UUIDField(
        description = "unique identifier of this attribute value",
        required    = True
    ),
    'original': UUIDField(
        description = "reference to a disabled previous attribute value that is now replaced by this one"
    ),
    'typename': attributetypename_t,
    'asset': fields.String(
        attribute = "asset_uuid",
        description = "reference to the asset this attributes relates to"
    ),
    'value': fields.String(
        description = "string representation of a simple, unstructured attribute value"
    ),
    'data': fields.Raw(
        description = "complex data object instead of a simple value"
    ),
    'active': fields.Boolean(
        description = "indicates whether this attribute is active or it documents an inactive (e.g. old) value",
        required    = True,
        default     = True
    ),
    'is_id': fields.Boolean()
})



@api.route('/')
class _AttributeList(Resource):

    @api.marshal_with(attribute_t)
    @api.expect(pagination_parser)
    @api.expect(inactive_parser)
    def get(self):
        args = pagination_parser.parse_args()
        args.update(inactive_parser.parse_args())

        query = Attribute.query

        #if args.get('show_inactive') is not True:
        #    query = query.filter(Attribute.active == True)


        #TODO: query = query.filter.....
        attributes_list = query.paginate(
            args.get('page_no'),
            args.get('page_size') or app.config['pagination']['per_page_default'],
            app.config['pagination']['per_page_max']
        ).items

        return attributes_list


    #TODO: implement Attribute POST



@api.route('/<uuid>')
class _Attribute(Resource):
    """Represents the REST interface to Asset-specific Attributes"""

    @api.marshal_with(attribute_t)
    def get(self, uuid):
        
        #TODO: handling von aktiven/inaktiven Attributen, replacement-uuids, ...
        attribute = Attribute.query.filter(Attribute.uuid == str(uuid)).first_or_404()

        return attribute

    def post(self):
        pass


@api.route('/types')
class _AttributeTypeList(Resource):

    @api.expect(pagination_parser)
    @api.marshal_with(attributetype_t)
    def get(self):
        args = pagination_parser.parse_args()

        attributetypes_list = AttributeType.query.paginate(
            args.get('page_no'),
            args.get('page_size') or app.config['pagination']['per_page_default'],
            app.config['pagination']['per_page_max']
        ).items

        return attributetypes_list


@api.route('/types/<typename>')
class _AttributeType(Resource):

    @api.marshal_with(attributetype_t)
    def get(self, typename):

        attributetype = AttributeType.query.filter(AttributeType.typename == str(typename)).first_or_404()

        return attributetype
