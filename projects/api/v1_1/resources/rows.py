# -- rows.py --

# API functions to manage data rows

# EKU Power Drives GmbH 2019, Kristian Binder <kristian.binder@ekupd.com>

# -- external dependencies --
from flask_restplus import Namespace, Resource, fields
from flask import current_app as app, request
from uuid import UUID
import sqlalchemy.exc
import psycopg2.errors


# -- project dependencies --
from ..globals.pagination import pagination_parser
from ..globals.uuid import UUIDField
from .datatypes import typename_t
from models.row import Row



api = Namespace('Rows', description='manage data types used by data entries')


row_t_base = api.model('Row_base', {
    'uuid': UUIDField(
        description = "global row identifier"
    ),
    'typename': typename_t,
    'time_utc': fields.DateTime(
        description = "Time and date of data sampling",
        dt_format   = 'iso8601'
    ),
    'asset_uuid': UUIDField(
        description = "identifier of the subject asset"
    ),
    'source_uuid': UUIDField(
        description = "asset uuid of the source asset"
    )
})

row_t_full = api.inherit('Row_full', row_t_base, {
    'time_mono': fields.Float(
        description = "System Monotonic clock time of data sampling"
    ),
    'rcvtime_utc': fields.DateTime(
        description = "Time and date of data arrival at first data service instance",
        dt_format   = 'iso8601'
    ),
    'rcvtime_mono': fields.Float(
        description = "System Monotonic clock time of arrival at first data service instance"
    ),
    'data': fields.Raw(
        description = "actual data as a JSON object as specified in typename"
    )
})

rowlist_t_patch = api.model('Rowlist_patch', {
    'uuid': UUIDField,
    'status': fields.String(),
    'msg': fields.String()
})

@api.route('/')
class _RowList(Resource):

    @api.marshal_with(row_t_base)
    @api.expect(pagination_parser)
    def get(self):
        args = pagination_parser.parse_args()

        query = Row.query
        #TODO: filter

        rows_list = query.paginate(
            args.get('page_no'),
            args.get('page_size') or app.config['pagination']['per_page_default'],
            app.config['pagination']['per_page_max']
        ).items

        return rows_list


    @api.marshal_with(row_t_full)
    @api.expect(row_t_full)
    def post(self):
        body = request.json

        row = Row(
            time_utc        = body.get('time_utc'),
            time_mono       = body.get('time_mono'),
            rcvtime_utc     = body.get('rcvtime_utc'),
            rcvtime_mono    = body.get('rcvtime_mono'),
            source_uuid     = body.get('source_uuid'),
            asset_uuid      = body.get('asset_uuid'),
            rcvnode_uuid    = body.get('rcvnode_uuid'),
            typename        = body.get('typename'),
            data            = body.get('data')
        )
        row.save()

        return row, 201


    @api.marshal_with(rowlist_t_patch)
    @api.expect([row_t_full])
    def patch(self):
        #TODO: allow changing of individual rows?
        #  current implementation does only add new rows
        out = []
        failed = False
        body = request.json

        for jrow in body:
            row = None
            msg = ""
            try:
                row = Row(
                    uuid             = jrow.get('uuid'),
                    time_utc         = jrow.get('time_utc'),
                    time_mono        = jrow.get('time_mono'),
                    rcvtime_utc      = jrow.get('rcvtime_utc'),
                    rcvtime_mono     = jrow.get('rcvtime_mono'),
                    source_uuid      = jrow.get('source_uuid'),
                    asset_uuid       = jrow.get('asset_uuid'),
                    rcvnode_uuid     = jrow.get('rcvnode_uuid'),
                    typename         = jrow.get('typename'),
                    data             = jrow.get('data')
                )
                row.save()
            except sqlalchemy.exc.IntegrityError as e:
                # if a row with this UUID already exists on our side, the insert will throw a unique violation
                assert isinstance(e.orig, psycopg2.errors.UniqueViolation)
                msg = "Ignore already synced row"
                # policy: keep local versions - ignore and proceed
                pass

            except Exception as e:
                msg = "Exception during PATCH: {e}".format(e=str(e))
                failed = True
                pass

            finally:
                out.append({'uuid': jrow['uuid'], 'status': 'failed' if failed else 'ok', 'msg': msg})


        if failed:
            return out, 400
        else:
            return out, 202




@api.route('/<uuid>')
class _Row(Resource):

    @api.marshal_with(row_t_full)
    def get(self, uuid):
        row = Row.query.filter(Row.uuid == uuid).first_or_404()

        return row

    #TODO: patch, delete
