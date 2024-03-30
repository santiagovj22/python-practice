# -- relations.py --

# API endpoints for managing relations between assets

# EKU Power Drives GmbH 2019, Kristian Binder <kristian.binder@ekupd.com>

# -- external dependencies --
from flask_restplus import Namespace, Resource, fields, reqparse, inputs
from flask import current_app as app, abort
from sqlalchemy import or_

# -- project dependencies --
from ..globals.pagination import pagination_parser
from ..globals.inactive import inactive_parser
from ..globals.uuid import UUIDField

from models.relation import Relation, RelationType
from models.asset import Asset


api = Namespace('Relations', description='relations between assets')


relationtypename_t = fields.String(
    description = "relation type name / URN",
    example     = 'equipment:installed-in',
    required    = True
)

relationtype_t = api.model('RelationType', {
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

relation_t = api.model('Relation', {
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
    'asset_src': UUIDField(
        description = "the UUID of the asset this relation originates at (source)",
        attribute   = 'asset_src.uuid',
        required    = True
    ),
    'asset_src_title': fields.String(
        description = "the title of the asset this relation originates at (source)",
        attribute   = 'asset_src.title'
    ),
    'asset_dst': UUIDField(
        description = "the UUDI of the asset this relation is pointing at (destination)",
        attribute   = 'asset_dst.uuid',
        required    = True
    ),
    'asset_dst_title': fields.String(
        description = "the title of the asset this relation is pointing at (destination)",
        attribute   = 'asset_dst.title'
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
    help = 'can only be used in requests where an asset id is defined. Will only return relations \'inbound\' or \'outbound\' from this asset\'s view'
)

@api.route('/')
class _RelationList(Resource):

    @api.expect(pagination_parser)
    @api.expect(relationlist_parser)
    @api.expect(inactive_parser)
    @api.marshal_with(relation_t)
    def get(self, asset_id=None):
        args = pagination_parser.parse_args()
        args.update(relationlist_parser.parse_args())
        args.update(inactive_parser.parse_args())

        query = Relation.query

        #if args.get('show_inactive') is not True:
        #    query = query.filter(Relation.active == True)

        if asset_id is not None:
            asset = Asset.from_id(asset_id)
            query = query.filter(or_(Relation.asset_dst_uuid == asset.uuid, Relation.asset_src_uuid == asset.uuid))

        if args.get('type') is not None:
            query = query.filter(Relation.typename == args['type'])

        if args.get('direction') is not None and isinstance(asset, Asset):
            if asset_id is None:
                abort(400, "The 'direction' filter can only be used when querying for relations based on a given asset id")
            else:
                if args['direction'] == 'inbound':
                    query = query.filter(Relation.asset_dst_uuid == asset.uuid)
                elif args['direction'] == 'outbound':
                    query = query.filter(Relation.asset_src_uuid == asset.uuid)
                else:
                    abort(400, "The 'direction' filter does only accept values 'inbound' or 'outbound'")

        relations_list = query.paginate(
            args.get('page_no'),
            args.get('page_size') or app.config['pagination']['per_page_default'],
            app.config['pagination']['per_page_max']
        ).items

        return relations_list

    #TODO: implement POST
    def post(self):
        pass



@api.route('/<uuid>')
@api.param('uuid', description='the relations UUID', _in='query')
class _Relation(Resource):

    @api.marshal_with(relation_t)
    def get(self, uuid):
        return {'shouldbe': 'a single relation', 'uuid': uuid}


@api.route('/types')
class _RelationTypeList(Resource):

    @api.expect(pagination_parser)
    @api.marshal_with(relationtype_t)
    def get(self):
        args = pagination_parser.parse_args()

        attributetypes_list = RelationType.query.paginate(
            args.get('page_no'),
            args.get('page_size') or app.config['pagination']['per_page_default'],
            app.config['pagination']['per_page_max']
        ).items

        return attributetypes_list


@api.route('/types/<typename>')
class _RelationType(Resource):

    @api.marshal_with(relationtype_t)
    def get(self, typename):

        relationtype = RelationType.query.filter(RelationType.typename == str(typename)).first_or_404()

        return relationtype