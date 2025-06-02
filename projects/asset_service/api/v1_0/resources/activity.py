# -- activity.py --

# API endpoints handling activity (aka logs)

# EKU Power Drives GmbH 2019, Kristian Binder <kristian.binder@ekupd.com>

# -- external dependencies --
from flask_restplus import Namespace, Resource, fields
from flask import current_app as app

# --project dependencies --
from ..globals.pagination import pagination_parser
from ..globals.uuid import UUIDField

from models.activity import ActivityType, SubjectType, Activity


api = Namespace('Activity', description='logged activities in asset management')


activity_t = api.model('Activity', {
    'uuid': UUIDField(
        description = "Unique identifier"
    ),
    'type': fields.String(
        description = "Type of activity",
        enum        = ActivityType._member_names_
    ),
    'subject_type': fields.String(
        description = "Type of Activity Subject",
        enum        = SubjectType._member_names_
    ),
    'subject_uuid': UUIDField(
        description = "UUID of the subject of the activity"
    )
})


@api.route('/')
#TODO: handle the additional routes to filter activity ba asset/attribute/relation/... uuid
#@api.route('/assets/<identifier>')
#@api.route('/attributes/<identifiers>')
class _ActivityList(Resource):

    @api.expect(pagination_parser)
    @api.marshal_with(activity_t)
    def get(self):
        args = pagination_parser.parse_args()

        query = Activity.query

        activity_list = query.paginate(
            args.get('page_no'),
            args.get('page_size') or app.config['pagination']['per_page_default'],
            app.config['pagination']['per_page_max']
        ).items

        return activity_list


@api.route('/<activity>')
class _Activity(Resource):

    @api.marshal_with(activity_t)
    def get(self):
        #TODO: display a single activity
        return None
