# -- __init__.py --

# global variables for the 'models' module

# EKU Power Drives GmbH 2019, Kristian Binder <kristian.binder@ekupd.com>

# -- external dependencies --
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()


class BaseModel(db.Model):
    __abstract__ = True

    ## global attributes / wrapper functions common for all
    ## Model classes can go here
