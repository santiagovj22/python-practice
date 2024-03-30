# -- __init__.py --

# global variables for the 'models' module

# EKU Power Drives GmbH 2019, Kristian Binder <kristian.binder@ekupd.com>

# -- external dependencies --
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData
import os,sys

# -- internal dependencies --
from benchmarking import decorator_viztracer

db = SQLAlchemy()
meta = MetaData()#schema = 'data_raw')#schema = 'data_raw') #(schema = 'data_raw')

#@decorator_viztracer
def getMetaData():
    ''' returns sqlalchemy metadata from cache (via pickle) or from database (via reflection) '''
    
    meta = MetaData() # -> I don't understand why I need this initialization here ? If not it says: local variable 'meta' referenced before assignment
    meta.reflect(bind = db.engine)#,schema = 'data_raw')
    print("loaded metadata from database")
    return meta




# All table classes created at runtime are stored in this dict
signals_dict = {}
views_dict = {}

class BaseModel(db.Model):
    __abstract__ = True

    ## global attributes / wrapper functions common for all
    ## Model classes can go here
