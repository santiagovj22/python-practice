# -- signals.py --

# API functions to manage signals

# --external dependencies --

from flask_restplus import Namespace, Resource, fields, reqparse, inputs, marshal, abort
from flask import current_app as app, request
from models import meta_source
import sqlalchemy.exc

# -- project dependencies --
from ..globals.pagination import paginate_with
from ..globals.uuid import UUIDField
from models.signal import get_class_by_tablename,createTable,createMaterializedView
from models.meta_source import MetaSource
from models.meta_quality import MetaQuality
from models import db,signals_dict
from ..globals.uuid import UUIDField
from benchmarking import decorator_viztracer
api = Namespace('Signals', description='manage timescale Signals')

######################################  API models #############################################
signal_meta = api.model('Signal Meta Data:', {
    'name': fields.String(description='Signal name'),
    'datatype': fields.String(description='Datatype of signal')  
})
#'datatype': fields.String(required=True, description='Datatype of signal')
signal_active = api.model('Signal Active', {
    'asset': UUIDField(description = "asset uuid"),
    'fatnode': UUIDField(description = "fatnode uuid"),
    '_from': fields.DateTime(description='Time UTC', dt_format = 'iso8601'),
    '_to': fields.DateTime(description='Time UTC', dt_format = 'iso8601'),
})


signal_sample = api.model('timeseries raw data point', {
    'uuid': UUIDField(description = "global row identifier"),
    'time_utc':fields.DateTime(description='Time UTC', dt_format = 'iso8601'),
    'time_mono':fields.Integer(description='Time mono'),
    'rcvtime_mono':fields.Integer( description='RcvTime mono'),
    'asset': UUIDField(description = "asset identifier"),
    'meta_source': fields.Integer( description='Source id'),
    'meta_quality': fields.Integer( description='Quality id'),
    'sync_prio': fields.Integer(description='Sync prio'),
    'data': fields.Integer(description='Value') 
})

signal_sample_list = api.model('list of timeseries raw data points',{
    'datapoints': fields.List(
        fields.Nested(signal_sample)
    )
})

signal_aggregation = api.model('timeseries aggregated data point', {
    'asset_uuid': UUIDField(description = 'asset uuid'),
    'bucket':fields.DateTime(description='bucket Time UTC', dt_format = 'iso8601'),
    'avg':fields.Float(description='avg value in bucket'),
    'max':fields.Float( description='max value in bucket'),
    'min': fields.Float(description = "min value in bucket"),
    'count': fields.Integer( description='number of datapoints in this bucket'),
    'first_value': fields.Float( description='First value'),
    'last_value': fields.Float(description='Last value'),
    'stddev': fields.Float(description='Standard deviation in bucket'),
    'first_time_utc': fields.DateTime(description='First data point in bucket', dt_format = 'iso8601'),
    'last_time_utc': fields.DateTime(description='last data point in bucket', dt_format = 'iso8601')
})


##################################################### Parsers #####################################################
signal_meta_parser = reqparse.RequestParser()
signal_meta_parser.add_argument('datatype',
    choices=('float','integer', 'varchar','jsonb' ),
    required = True,
    help = 'Datatype of Signal'
)
signal_meta_parser.add_argument('Chunk Size',
    required = False,
    help = 'Not implemented yet!! Must be valid postgres INTERVAL type. Example: 6 hours'
)
# signal parser: Default parser for raw signals. Other parser are inherited from this
#
#
signal_parser = reqparse.RequestParser() #--> curl --data "date=2012-01-01T23:30:00+02:00" localhost:5000/myGet
signal_parser.add_argument('assets_uuids',
    action="append",
    required = True,
    help = 'List of asset uuids'
)
signal_parser.add_argument('from',
    type=inputs.datetime_from_iso8601,
    required = True,
    help = 'Start of time frame (format: iso8601, ex:2021-01-01T23:30:00+02:00)'
)
signal_parser.add_argument('to',
    type=inputs.datetime_from_iso8601,
    required = True,
    help = 'End of time frame (format: iso8601, ex:2021-05-01T23:30:00+02:00)'
)
signal_parser.add_argument('orderBy',
    #type= fields.String,
    choices = ('DESC','ASC'),
    default = 'DESC',
    help = 'Order by time_utc DESC or ASC'
)

# signal aggregation parser: Parser for buckets
#
signal_aggregation_parser = signal_parser.copy()
signal_aggregation_parser.add_argument('aggregations',
    type = list,
    #choices=('avg','max', 'min' ),
    action="split",
    required = True,
    help = 'List of aggregations types which are returned'
)   
signal_aggregation_parser.add_argument('bucketsize',
    choices = ('1 day', '1 hour', '15 min', '5 min'),
    required = True,
    help = 'bucket size'
)

# signal active parser: Parser to check which assets where connected to given source, based on the given signal
#
signal_active_parser = signal_parser.copy() #--> curl --data "date=2012-01-01T23:30:00+02:00" localhost:5000/myGet
signal_active_parser.remove_argument('assets_uuids')
signal_active_parser.add_argument('source_uuid',
    required = True,
    help = 'UUID of source'
)
signal_active_parser.add_argument('bucketsize',
    choices = ('1 day', '1h', '15 min', '5 min'),
    default = '1 day',
    help = 'bucket size'
)
signal_active_parser.add_argument('invert',
    type = bool,
    default = False,
    help = 'If True: returns active time of asset, else returns inactive time'
)

###################################### Endpoints ####################################################

#Remove this class only for testing
class smallSignalClass():
        def __init__(self,name):
            self.name = name  

@api.route('/')
class SignalCollection(Resource):

    @api.marshal_with(signal_meta)
    def get(self):
        ''' Returns a list of all available signals '''
        
        names = []
        for key in signals_dict:
            names.append(smallSignalClass(key))
        
        return names

#@api.route('/<uuid>/memberships')
@api.route('/<string:asset_uuid>')
class SignalsPerAsset(Resource):
    @api.marshal_with(signal_meta) 
    def get(self):
        ''' Returns a list of available signals for the given asset '''
        return []  

# --> do parsing in class: https://www.jameskozlowski.com/index.php/2018/04/14/a-simple-flask-api-example/

@api.route('/<string:signalname>/samples')
class SignalRaw(Resource):
    
    @paginate_with(api,
        embedded_model = signal_sample,
        embedded_key = 'signalname'
    )
    @api.expect(signal_parser)
    def get(self,signalname):
        ''' Returns data points from one signal '''
        args = signal_parser.parse_args()
        #if has_request_context():
        table = get_class_by_tablename(signalname)

        if args['orderBy'] != 'ASC':
            orderBy = table.time_utc.desc
        else:
            orderBy = table.time_utc.asc
        
        return table.query.filter(table.asset.in_(args['assets_uuids'])).\
                           filter(table.time_utc.between(args['from'],args['to'])).\
                           order_by(orderBy())
    
    #@api.marshal_with(signal_meta)
    @api.expect(signal_meta_parser)
    @api.response(404, 'Signal already exists')
    def put(self, signalname):
        ''' Creates a new signal '''

        signalname = signalname.lower()
        args = signal_meta_parser.parse_args()

        table = get_class_by_tablename(signalname)
        if table == None:
            createTable(signalname,args['datatype'])
            #createMaterializedView(get_class_by_tablename(signalname),'view'+signalname)

        return 201
        
    @api.marshal_with(signal_sample_list)
    @api.expect(signal_sample_list)
    @api.response(409, 'Duplicate identifier')
    def post(self,signalname):
        ''' Inserts datapoints into signal table. Depending on number of datapoints single or bulk inserts are used '''
        
        points = request.json['datapoints']
        if len(points) == 1:
            # make single insert
            for point in points:  
                point = marshal(point,signal_sample)
                try:
                    point = get_class_by_tablename(signalname).single_insert(**point)
                    return 201

                except sqlalchemy.exc.IntegrityError as e:
                    msg = str(e).split('\n')[1].lstrip('DETAIL:  ')
                    abort(409, message=msg)
                except Exception as e:
                    abort(409, message=e)
        else:
            # make bulk inserts
            datapoints = []
            for point in points:
                point = marshal(point,signal_sample)
                datapoints.append(point)    
            
            try:
                get_class_by_tablename(signalname).bulk_insert(datapoints)
                return 201

            except sqlalchemy.exc.IntegrityError as e:
                msg = str(e).split('\n')[1].lstrip('DETAIL:  ')
                abort(409, message=msg)
            except Exception as e:
                abort(409, message=e)
        

@api.route('/<string:signalname>/aggregations')
class SignalAggregation(Resource):
    
    #@api.expect(signal_aggregation_parser)
    @api.marshal_with(signal_aggregation)
    def get(self,signalname):
        ''' returns buckets for given signal '''    

# TODO: Insted of raw sql use database function ? -> db.session.query(func.public.getassetsfromfatnode(fatnode[0].id,'15 minutes','2020-10-01T23:30:00+02:00','2021-02-01T23:30:00+02:00')).all())
# Problem: When using functions the columns (keys) of the returned RowProxy Object are missing. I think you have to use sqlalchemy's outparam() and bindparam() parameters. But could't get it running
# A few links that I used:
# https://riptutorial.com/sqlalchemy/example/6614/converting-a-query-result-to-dict
# functions with sqlalchemyhttps://www.fullstackpython.com/sqlalchemy-sql-functions-examples.html
# sqlalchemy generic functions: https://docs.sqlalchemy.org/en/14/core/functions.html#sqlalchemy.sql.functions.GenericFunction
# https://docs.sqlalchemy.org/en/14/core/tutorial.html#functions
# https://stackoverflow.com/questions/3563738/stored-procedures-with-sqlalchemy
# https://www.py4u.net/discuss/17218
# final solution: https://stackoverflow.com/questions/17972020/how-to-execute-raw-sql-in-flask-sqlalchemy-app
@api.route('/<string:signalname>/active')
class SignalActive(Resource):
    
    @paginate_with(api,
        embedded_model = signal_active,
        embedded_key = 'signalname', 
    )
    @api.expect(signal_active_parser)
    def get(self,signalname):
        ''' Returns online or offline status of assetes connected to given source. 
        !!! Currently daily buckets are always used + the signal oilandgas__frac_pump_oph_esc_mode_active is always used !!! '''
        
        args = signal_active_parser.parse_args()

        # from fatnode uuid get meta_source id
        sources = MetaSource.getSourceIdFromFatnodeUUID(args['source_uuid']).all()
        
        meta_source_Ids = []
        for id in sources:
            meta_source_Ids.append(id.id)
        meta_source_Ids_tuple = tuple(meta_source_Ids)
       
        # FIXME: This query recognizes when meta_source of a asset changes. But it should only check if meta_source->fatnode changes. 
        #        For now we only have the key "fatnode" in meta_source, so it works. But if we add CAN bus or other keys then we have to fix this.
        resultproxy = db.session.execute("""
        SELECT asset, (meta_source.source->>'fatnode')::uuid AS fatnode, _from,_to
        FROM(
            SELECT asset,sub3.meta_source,
                CASE WHEN new_start IS NULL THEN lag(new_start) OVER (PARTITION BY asset ORDER BY bucket) ELSE new_start END AS _from,
                CASE WHEN new_end IS NULL THEN lead(new_end) OVER (PARTITION BY asset ORDER BY bucket) ELSE new_end END AS _to
            FROM(
                SELECT asset,sub2.meta_source,bucket,
                        CASE WHEN before_data IS NULL OR(before_source != meta_source AND min_ts IS NOT NULL) THEN min_ts ELSE NULL END AS new_start,
                        CASE WHEN after_data IS NULL OR(after_source != meta_source AND min_ts IS NOT NULL) THEN max_ts ELSE NULL END AS new_end
                FROM(
                    SELECT asset,sub1.meta_source,bucket,before_data,after_data,before_source,after_source, min_ts, max_ts
                    FROM
                        (SELECT asset,sub0.meta_source,gap_bucket AS bucket,min_ts, max_ts,
                                lag(min_ts) OVER (PARTITION BY asset,meta_source ORDER BY gap_bucket) AS before_data,
                                lead(min_ts) OVER (PARTITION BY asset,meta_source ORDER BY gap_bucket) AS after_data,
                                lag(meta_source) OVER (PARTITION BY asset,meta_source ORDER BY gap_bucket) AS before_source,
                                lead(meta_source) OVER (PARTITION BY asset,meta_source ORDER BY gap_bucket) AS after_source     
                            FROM(
                                SELECT  asset,meta_source,time_bucket_gapfill('1 day', time_utc)AS gap_bucket, min(time_utc) AS min_ts, max(time_utc) AS max_ts
                                FROM data_raw.oilandgas__frac_pump_oph_esc_mode_active 
                                WHERE meta_source IN :sources AND time_utc BETWEEN :time_from AND :time_to
                                GROUP BY asset,meta_source,gap_bucket
                                ORDER BY gap_bucket ASC
                            )sub0
                        )sub1
                    WHERE min_ts IS NOT NULL AND (before_data IS NULL OR after_data IS NULL OR before_source != meta_source OR after_source != meta_source) 
                    )sub2
                )sub3 
            )sub4 LEFT JOIN meta_source ON sub4.meta_source = meta_source.id  --get fatnode uuid from meta_source
        GROUP BY asset,meta_source.id,_from, _to
        ORDER BY asset,_from
        """,{'signalname':'data_raw.fuelrate','sources':meta_source_Ids_tuple,'time_from':args['from'],'time_to':args['to']})
        #  
        # convert returned resultproxy to dict keyed by column names
        list = []
        for r in resultproxy:
            #print(r[0]) # Access by positional index
            list.append(dict(r.items())) 
        
        return list

######################################## Database functions ########################################



#def getTable(tablename):
#    ''' returns the sqlalchemy table with the request tablename.
#        If the corresponding table doesn't exist, it creates a new one 
#    '''
#    meta1 = getMetaData()
#    if 'data_raw.' + tablename in meta1.tables:
#        print('existed')
#    else:
#        print('create table')
#        createTable(tablename)
#        meta1 = getMetaData()
#        print('getTable',type( meta1.tables.get('data_raw.' + tablename)))
#    return meta1.tables.get('data_raw.' + tablename) # return the table object
  


