# --signal.py --

# model of a sophia data signal

# EKU Power Drives GmbH 2021, Matthias Epple <matthias.epple@ekupd.com>

# -- external depenencies --
from datetime import time

from sqlalchemy.orm import relationship
from sqlalchemy.sql.schema import Column, MetaData
from models import meta_source

import sqlalchemy.dialects.postgresql as pgtypes
from sqlalchemy import event,DDL,Index, func,Table,INTEGER,ForeignKey
from sqlalchemy.dialects.postgresql import DOUBLE_PRECISION, VARCHAR,JSONB

from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.ext.declarative import declared_attr

from models.view_factory import create_materialized_view, CreateView
# -- project dependencies --
from . import db, BaseModel, meta, signals_dict,views_dict


class Signal(BaseModel):
    __abstract__ = True

    uuid = db.Column(pgtypes.UUID, server_default = db.text('uuid_generate_v4()'))
    time_utc = db.Column(pgtypes.TIMESTAMP,primary_key=True) 
    time_mono = db.Column(pgtypes.BIGINT)
    rcvtime_mono = db.Column(pgtypes.BIGINT)
    asset = db.Column(pgtypes.UUID)
    sync_prio = db.Column(pgtypes.INTEGER)

    # in abstract classes foreign keys must be defined like the following:
    @declared_attr
    def meta_source(cls):
        return db.Column(pgtypes.BIGINT, ForeignKey('public.meta_source.id'),primary_key=True)

    @declared_attr
    def meta_quality(cls):
        return db.Column(pgtypes.BIGINT, ForeignKey('public.meta_quality.id'))
    

    
    @classmethod
    def single_insert(cls, **kwargs):
        point = cls(**kwargs)
        db.session.add(point)
        db.session.commit()
        return point

    # if bulk_insert is too slow there are other options: https://docs.sqlalchemy.org/en/13/faq/performance.html#i-m-inserting-400-000-rows-with-the-orm-and-it-s-really-slow
    # return_defaults = True also reduces performance ! 
    @classmethod
    def bulk_insert(cls,list):
        """ Individual INSERT statements in "bulk", but calling upon last row id
        @param list: list of marshal objects which describe the corrsponding Signal class 
        """
        obj_list = []
        for point in list:
            obj_list.append(cls(**point))
        
        # do we need try,except,rollback here ? 
        db.session.bulk_save_objects(obj_list,return_defaults=True,)
        db.session.commit()
  
    # don't do it like this! 
    def save(self):
        db.session.add(self)
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise e

class Signal_Float(Signal):
    __abstract__ = True
    data = db.Column(pgtypes.FLOAT)

class Signal_Integer(Signal):
    __abstract__ = True
    data = db.Column(pgtypes.INTEGER)

class Signal_Varchar(Signal):
    __abstract__ = True
    data = db.Column(pgtypes.VARCHAR)

class Signal_JSONB(Signal):
    __abstract__ = True
    data = db.Column(pgtypes.JSONB)


def get_class_by_tablename(tablename):
  """Return class reference mapped to table.

  :param tablename: String with name of table.
  :return: Class reference or None.
  """
  # catch not available
  return signals_dict.get(tablename)

class MaterializedView(BaseModel):
    __abstract__ = True
   
# shouldn't we use this to create tables ????????    
#from sqlalchemy.schema import CreateTable
#with engine.connecmyTable = create_materialized_view(vit() as conn:
#    conn.execute(CreateTable(mytable))

#DDL String substitutions: https://www.kite.com/python/docs/sqlalchemy.DDL
#%(table)s  - the Table name, with any required quoting applied
#%(schema)s - the schema name, with any required quoting applied
#%(fullname)s - the Table name including schema, quoted if needed


def createTable(tablename, datatype, existsInDB = False):
    ''' creates a sqlalchemy table + materialized views during runtime and adds this new table to database '''

    # create table class at runtime
    #'__table_args__': {'autoload':True},
    return_value = False
    SignalClass = None
    if datatype == "integer" or isinstance(datatype, INTEGER)  :
        SignalClass = Signal_Integer
    elif datatype == "float" or isinstance(datatype, DOUBLE_PRECISION):
        SignalClass = Signal_Float
    elif datatype == "varchar" or isinstance(datatype, VARCHAR):
        SignalClass = Signal_Varchar
    elif datatype == 'jsonb' or isinstance(datatype, JSONB):
        SignalClass = Signal_JSONB
    
    if SignalClass is not None:
        attr_dict = {'__tablename__': tablename,  
                     '__table_args__': {"schema": "data_raw"}
                    }
        myClass = type(tablename, (SignalClass,),attr_dict)

        if not existsInDB:
            # create Index
            Index(tablename + "_asset_time_utc_index", myClass.asset, myClass.time_utc.desc())
            # create Hypertable 
            event.listen(myClass.__table__,'after_create',DDL("""SELECT create_hypertable('%(fullname)s', 'time_utc', if_not_exists => TRUE);"""))
            # add reorder policy
            event.listen(myClass.__table__,'after_create',DDL("""SELECT add_reorder_policy('%(fullname)s', '%(table)s_asset_time_utc_index')"""))
            # add compression
            event.listen(myClass.__table__,'after_create', DDL("""ALTER TABLE %(fullname)s SET(
                                                               timescaledb.compress,
                                                               timescaledb.compress_segmentby = 'asset, meta_source, meta_quality', 
                                                               timescaledb.compress_orderby = 'time_utc DESC'
                                                               );
                                                               SELECT add_compression_policy('%(fullname)s', INTERVAL '3 months')              
                                                               """)
                    ) 
        signals_dict[tablename] = myClass
        meta.create_all(db.engine,tables=[myClass.__table__]) 
        return_value = True
    
    return return_value

def createMaterializedView(myClass, tablename):

    # Select statement for materialized view   
    query = db.select([myClass.asset.label('asset'),
                      func.time_bucket('5 minutes',myClass.time_utc).label('bucket'),
                      func.avg(myClass.data).label('avg'),
                      func.max(myClass.data).label('max'),
                      func.min(myClass.data).label('min'),
                      func.count(myClass.data).label('count'),
                      func.first(myClass.data, myClass.time_utc).label('first_value'),
                      func.last(myClass.data, myClass.time_utc).label('last_value'),
                      func.stddev(myClass.data).label('stddev'),
                      func.min(myClass.time_utc).label('first_time'),
                      func.max(myClass.time_utc).label('last_time'),]).group_by(myClass.asset, 'bucket')
    
    attr_dict = {'__table__': create_materialized_view(tablename, query, meta, True)}  
    
    # create view at runtime
    myView = type(tablename, (MaterializedView,), attr_dict)
    #event.listen(myClass.__table__,'after_create', DDL("""
    #                                                  SELECT add_continuous_aggregate_policy('%(fullname)s',
    #                                                  start_offset => NULL,
    #                                                  end_offset => INTERVAL '5 days',
    #                                                  schedule_interval => INTERVAL '1 day');
    #                                                  """))

    signals_dict[tablename] = myView
    
    #In the following line of code, normally there should be tables=[myView.__table__]. But it crashes with:
    #"Can't generate DDL for NullType(); did you forget to specify a type on this Column?"
    # This is because of the returntype of func.
    # return type of all functions:<sqlalchemy.sql.elements.ColumnClause>
    # ColumnClause is the immediate superclass of the schema-specific Column object
    # return type of asset: Column('asset', UUID()
    # --> I don't understand why it creates the myView, although I say create myClass.__table__
    meta.create_all(db.engine,tables=[myClass.__table__],checkfirst=True)
    #meta.reflect(bind = db.engine,views=True)
    
def reflectDatabase():
    #meta = MetaData()
    signals_dict.clear()
    views_dict.clear()

    # metadata.reflect() will only reflect the default schema(first in search path)
    # In order to reflect other schemas you need to call metadata.reflect() for each schema.
    # Working with schemas + tables with same name: https://stackoverflow.com/questions/47803343/reflecting-every-schema-from-postgres-db-using-sqlalchemy
    meta.reflect(bind = db.engine) # Only reflects schema public
    meta.reflect(bind = db.engine,schema = 'data_raw')# Only reflects schema data_raw
    
    for table in meta.sorted_tables:
        if table.schema == 'data_raw':
            createTable(table.name,table.columns['data'].type, True)

