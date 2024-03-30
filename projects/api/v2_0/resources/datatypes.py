# -- datatypes.py --

# API functions to manage data types

# EKU Power Drives GmbH 2019, Kristian Binder <kristian.binder@ekupd.com>

# -- external dependencies --
from flask_restplus import Namespace, Resource, fields
from flask import current_app as app, url_for

# -- project dependencies --
from ..globals.pagination import pagination_parser
from ..globals.uuid import UUIDField

from models.datatype import DataType


api = Namespace('DataTypes', description='manage data types used by data entries')

schema_url_base = '/schemas/'

class SchemaUrl(fields.Raw):
    def format(self, value):
        return schema_url_base + value.replace(':', '/') + '.json'

typename_t = fields.String(
    description = "unambiguous global identifier for this type",
    required    = True,
    example     = 'oilandgas:frac-pump:oph:manual-mode.1'
)

datatype_t_base = api.model('DataType_base', {
    'typename': typename_t,
    'display_name': fields.String(
        description = "Title of this data type to be shown in user interface",
        required    = True
    )
})

datatype_t_full = api.inherit('DataType_full', datatype_t_base, {
    'description': fields.String(
        description = "a descriptive text, explaining the usage and meaning in more detail"
    ),
#    'schema_url': SchemaUrl(attribute = 'typename')
})


@api.route('/')
class _DataTypeList(Resource):

    @api.marshal_with(datatype_t_base)
    @api.expect(pagination_parser)
    def get(self):
        args = pagination_parser.parse_args()

        query = DataType.query

        types_list = query.paginate(
            args.get('page_no'),
            args.get('page_size') or app.config['pagination']['per_page_default'],
            app.config['pagination']['per_page_max']
        ).items

        return types_list

    #TODO: put, (post?)


@api.route('/<typename>')
class _DataType(Resource):

    @api.marshal_with(datatype_t_full)
    def get(self, typename):
        type = DataType.query.filter(DataType.typename == typename).first_or_404()

        return type


    #TODO: patch, delete
