# -- sync.py --

# API functions to manage data sync

# EKU Power Drives GmbH 2019, Kristian Binder <kristian.binder@ekupd.com>

# -- external dependencies --
from flask_restplus import Namespace, Resource, fields
from flask import current_app as app, request
from uuid import UUID


# -- project dependencies --
from ..globals.pagination import pagination_parser
from ..globals.uuid import UUIDField
from .datatypes import typename_t
from models.row import Row
from models.sync import Sync


api = Namespace('Sync', description='get information about row synchronisation')

sync_t_full = api.model('Sync_full', {
    'uuid': UUIDField(
        description = "sync action identifier"
    ),
    'row': UUIDField(
        description = "row identifier"
    ),
    'time': fields.DateTime(
        description = "Time of synchronization attempt",
        dt_format = 'iso8601'
    ),
    'host': fields.String(
        description = "The remote host identifier as configured for this sync job"
    ),
    'result': fields.Raw(
        description = "The remote host's response for this sync"
    )
})

@api.route('/')
class _SyncList(Resource):

    @api.marshal_with(sync_t_full)
    @api.expect(pagination_parser)
    def get(self):
        args = pagination_parser.parse_args()

        q = Sync.query

        syncs_list = q.paginate(
            args.get('page_no'),
            args.get('page_size') or app.config['pagination']['per_page_default'],
            app.config['pagination']['per_page_max']
        ).items

        return syncs_list
