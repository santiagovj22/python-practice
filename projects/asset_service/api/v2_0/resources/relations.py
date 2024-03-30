# -- relations.py --

# API endpoints for managing relations between assets

# EKU Power Drives GmbH 2019, Kristian Binder <kristian.binder@ekupd.com>

# -- external dependencies --
from flask_restplus import Namespace, Resource, fields, reqparse, inputs
from flask import current_app as app, abort, request
from sqlalchemy import or_

# -- project dependencies --
from ..globals.pagination import paginate_with
from ..globals.inactive import inactive_parser
from ..globals.uuid import UUIDField

from .assets import asset_get_minimal

from models.relation import Relation, RelationType
from models.asset import Asset


api = Namespace('Relations', description='relations between assets')

class RelationLinks(fields.Raw):
    def __init__(self, **kwargs):
        fields.Raw.__init__(self, **kwargs)
        self.example = self.format('{asset uuid}')
            
    def format(self, value):
        return {'self': {'href': '/api/v2.0/relations/{}'.format(value)}}


class RelationTypeLinks(fields.Raw):
    def __init__(self, **kwargs):
        fields.Raw.__init__(self, **kwargs)
        self.example = self.format('{typename}')
            
    def format(self, value):
        return {'self': {'href': '/api/v2.0/relations/types/{}'.format(value)}}


relationtypename_t = fields.String(
    description = "relation type name / URN",
    example     = 'equipment:installed-in',
    required    = True
)

relationtype_get = api.model('RelationType', {
    '_links': RelationTypeLinks(attribute='typename'),
    'typename': relationtypename_t,
    'display_name': fields.String(),
    'description': fields.String(),
    'unique_src': fields.Boolean(
        description = "If true, the destination asset can only have this type of relation originating from one single source",
        required    = True,
        default     = False
    ),
    'unique_dst': fields.Boolean(
        description = "If true, the source asset can only have this type of relation pointing towards one single destination",
        required    = True,
        default     = False
    )
})

relation_get_minimal_inbound = api.model('Relation GET minimal inbound', {
    '_links': RelationLinks(attribute='uuid'),
    'typename': relationtypename_t,
    'asset_src': fields.Nested(asset_get_minimal,
        description = 'source asset'
    )
})

relation_get_minimal_outbound = api.model('Relation GET minimal outbound', {
    '_links': RelationLinks(attribute='uuid'),
    'typename': relationtypename_t,
    'asset_dst': fields.Nested(asset_get_minimal,
        description = 'destination asset'
    )
})

relation_get = api.model('Relation', {
    '_links': RelationLinks(attribute='uuid'),
    'uuid': UUIDField(
        description = "unique identifier of this relation",
        required = True
    ),
    'original': UUIDField(
        description = "the UUID of the original relation in case this relation is the replacement of a previous relation",
        attribute   = 'original.uuid',
        default     = None
    ),
    'replaced_by': fields.List(
        UUIDField(
            description = "if this is an inactive relation, this field can be used to link to other versions of this relation",
            attribute   = 'uuid',
            default     = None
        )
    ),
    'typename': relationtypename_t,
    'asset_src': fields.Nested(asset_get_minimal,
        description = 'source asset'
    ),
    'asset_dst': fields.Nested(asset_get_minimal,
        description = 'destination asset'
    ),
    'value': fields.String(
        description = "an optional value (string representation) describing this relation"
    ),
    'data': fields.Raw(
        description = "an optional data structure (object / dict), describing this relation"
    ),
    'active': fields.Boolean(
        description = "mark this relation as active or inactive (planned/archived)",
        required    = True
    )
})

relationlist_parser = reqparse.RequestParser()
relationlist_parser.add_argument('type',
    help = 'only return relations matching the given relation type'
)
relationlist_parser.add_argument('direction',
    choices = ('inbound', 'outbound'),
    help = 'can only be used in requests where an asset id is defined. Will only return relations \'inbound\' or \'outbound\' from this asset\'s view'
)
relationlist_parser.add_argument(inactive_parser.args[0])



@api.route('/')
class _RelationList(Resource):

    @paginate_with(api,
        embedded_model = relation_get,
        embedded_key = 'relations'
    )
    @api.expect(relationlist_parser)
    @api.response(400, 'Bad filter')
    # def get(self, asset=None):
    def get(self, identifier=None):
        """returns a list of relations"""
         
        args = relationlist_parser.parse_args()
        
        query = Relation.query

        if not args['show_inactive']:
            query = query.filter(Relation.active == True)

        if identifier is not None:
            asset = Asset.from_id(identifier)
            if asset is None:
                abort(404, message='No asset for this identifier')
            else:
                query = query.filter(or_(Relation.asset_dst_uuid == asset.uuid, Relation.asset_src_uuid == asset.uuid))

        if args['type'] is not None:
            query = query.filter(Relation.typename == args['type'])

        if args['direction'] is not None:
            if asset is None:
                abort(400, "The 'direction' filter can only be used when querying for relations based on a given asset id")
            else:
                if args['direction'] == 'inbound':
                    query = query.filter(Relation.asset_dst_uuid == asset.uuid)
                else:
                    query = query.filter(Relation.asset_src_uuid == asset.uuid)
        
        return query

    #TODO: implement POST
    def post(self):
        pass


@api.route('/<uuid>')
@api.param('uuid', description='the relations UUID', _in='query')
class _Relation(Resource):

    @api.marshal_with(relation_get)
    def get(self, uuid):
        """returns a relation"""
        # return {'shouldbe': 'a single relation', 'uuid': uuid} TODO what is this?
        relation = Relation.query.get(uuid)
        return relation


@api.route('/types')
class _RelationTypeList(Resource):

    @paginate_with(api,
        embedded_model = relationtype_get,
        embedded_key = 'relations_types'
    )
    def get(self):
        """returns a list of relation types"""
        return RelationType.query


@api.route('/types/<typename>')
@api.param('typename', description='the relation type\'s name')
class _RelationType(Resource):

    @api.marshal_with(relationtype_get)
    def get(self, typename):
        """returns the relation type"""

        relationtype = RelationType.query.filter(RelationType.typename == str(typename)).first_or_404()

        return relationtype