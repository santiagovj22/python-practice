# -- identifiers.py --

# API endpoints for handling alternative identifiers of assets

# EKU Power Drives GmbH 2019, Kristian Binder <kristian.binder@ekupd.com>

# -- external dependencies --
from flask_restplus import Namespace, Resource, fields
from flask import current_app as app

# -- project dependencies --
from ..globals.pagination import pagination_parser
from ..globals.uuid import UUIDField

from models.identifier import Identifier, IdentifierType


api = Namespace('Identifiers', description='alternative asset identifiers')


class IdentifierListToDictMapper():
    """reshapes the list of identifiers retrieved from the database
    into a dict, mapping the idtypes to their values.
    This is possible because an asset can only have one identifier of a type.
    The apply() function is called by flask_restplus' fields.Raw when passing
    this class as 'mask' attribute
    """
    def apply(idlist):
        return {id.typename: id.id_str for id in idlist}


idtypename_t = fields.String(
    description = "the typename / URN of the identifier",
    example     = 'eku:track-id',
    required    = True
)

idtype_t = api.model('IdentifierType', {
    'typename': idtypename_t,
    'display_name': fields.String(),
    'description': fields.String(),
    'regex':    fields.String(
        description = "a regular expression string matching a valid instance of this IdentifierType",
        example     = 'TN-([0-9A-F]{12})',
        required    = False
    )
})

identifier_t = api.model('Identifier', {
    'typename': idtypename_t,
    'id_str': fields.String(
        description = "the identifier in its string representation",
        example     = 'TN-0063-4816-1CD4',
        required    = True
    )
})



@api.route('/')
class _IdentifierList(Resource):

    @api.expect(pagination_parser)
    @api.marshal_with(identifier_t)
    def get(self):
        args = pagination_parser.parse_args()

        query = Identifier.query

        #TODO: query = query.filter....
        identifiers_list = query.paginate(
            args.get('page_no'),
            args.get('page_size') or app.config['pagination']['per_page_default'],
            app.config['pagination']['per_page_max']
        ).items

        return identifiers_list


@api.route('/<id_str>')
class _Identifier(Resource):

    @api.marshal_with(identifier_t)
    def get(self, id_str):

        identifier = Identifier.query.filter(Identifier.id_str == str(id_str)).first_or_404()

        return identifier



@api.route('/types')
class _IdentifierTypeList(Resource):

    @api.marshal_with(idtype_t)
    def get(self):
        args = pagination_parser.parse_args()

        query = IdentifierType.query

        #TODO: query = query.filter....
        idtypes_list = query.paginate(
            args.get('page_no'),
            args.get('page_size') or app.config['pagination']['per_page_default'],
            app.config['pagination']['per_page_max']
        ).items

        return idtypes_list


@api.route('/types/<typename>')
@api.param('typename', description='the identifier type name you wish to get more information about', _in='query')
class _IdentifierType(Resource):

    @api.marshal_with(idtype_t)
    def get(self, typename):

        idtype = IdentifierType.query.filter(IdentifierType.typename == str(typename)).first_or_404()

        return idtype
