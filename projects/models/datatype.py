# -- datatype.py --

# model of an attribute, describing the properties of an asset

# EKU Power Drives GmbH 2019, Kristian Binder <kristian.binder@ekupd.com>

# -- external dependencies --
from uuid import UUID, uuid4
from sqlalchemy.sql import func
import sqlalchemy.dialects.postgresql as pgtypes

# -- project dependencies --
from . import db, BaseModel


class DataType(BaseModel):

    __bind_key__ = 'data_legacy'
    __tablename__ = 'datatypes'

    typename = db.Column(
        pgtypes.VARCHAR(100),
        primary_key = True
    )

    display_name = db.Column(
        pgtypes.VARCHAR(100),
        nullable = False
    )

    description = db.Column(
        pgtypes.TEXT
    )

    autodiscover = db.Column(
        pgtypes.BOOLEAN
    )


    def __init__(self, typename, display_name=None, description=None, autodiscover=False):
        if isinstance(typename, str) and len(typename) <= 100:
            self.typename = typename
        else:
            raise ValueError("invalid type or length for 'typename': " + str(typename))

        if isinstance(display_name, str) and len(display_name) <= 100:
            self.display_name = display_name
        elif display_name is None:
            #create a default display_name
            dn = typename.split(':')
            self.display_name = dn[-1]
        else:
            raise ValueError("invalid type or length for 'display_name': " + str(display_name))

        if isinstance(description, str):
            self.description = description

        if autodiscover:
            self.autodiscover = True


    def save(self):
        db.session.add(self)
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise e
