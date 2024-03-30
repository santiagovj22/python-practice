# -- row.py --

# model of a data row

# EKU Power Drives GmbH 2019, Kristian Binder <kristian.binder@ekupd.com>

# -- external dependencies --
from uuid import UUID, uuid4
from sqlalchemy import orm, and_
from sqlalchemy.sql import func
import sqlalchemy.dialects.postgresql as pgtypes
import time
import pytz
from datetime import datetime
from dateutil import parser as dateparser

# -- project dependencies --
from . import db, BaseModel
from .datatype import DataType

class Row(BaseModel):

    __bind_key__ = 'data_legacy'
    __tablename__ = 'data'

    uuid = db.Column(
        pgtypes.UUID,
        primary_key = True,
        server_default = db.text('uuid_generate_v4()')
    )

    # measurement sampling time in the sampling device's system time / UTC time
    time_utc = db.Column(
        pgtypes.TIMESTAMP
    )

    # measurement sampling time in the sampling device's rate monotonic clock
    time_mono = db.Column(
        pgtypes.BIGINT
    )

    # UTC receive time of the measurement at the first data service node
    rcvtime_utc = db.Column(
        pgtypes.TIMESTAMP,
        server_default = db.text('NOW()')
    )

    # rate monotonic clock receive time of the measurement at the first data service node
    rcvtime_mono = db.Column(
        pgtypes.BIGINT,
        nullable = False
    )

    # asset ID of the device that brougth this measurement into the system (capture device)
    source_uuid = db.Column(
        'source',
        pgtypes.UUID,
        nullable = False,
    )

    # asset ID of the thing/asset/equipment this measurement is related to (physical signal source)
    asset_uuid = db.Column(
        'asset',
        pgtypes.UUID
    )

    # asset ID of the first machine storing the measurement in a SOPHIA database
    rcvnode_uuid = db.Column(
        'rcvnode',
        pgtypes.UUID
    )

    # type describes what schema to be used for input validation and data interpretation and to
    #   request specific data from the data service
    typename = db.Column(
        'type',
        pgtypes.VARCHAR(100),
        db.ForeignKey('datatypes.typename'),
        nullable = False
    )
    type = db.relationship(
        'DataType',
        backref = db.backref('rows', lazy = True)
    )

    # this is the actual data stored as a JSON file
    data = db.Column(
        pgtypes.JSONB
    )

    # data that was successfully validated against the JSON schema referred to by the datatype,
    #   will be marked with validated = True. Only validated data must be shown through the API
    #   to ensure the data service will always provide schema-compatible data.
    #   If the schema is not know at insertion time, the row can be validated at a later time.
    validated = db.Column(
        pgtypes.BOOLEAN,
        nullable = False,
        default = False
    )

    # TODO: have a field for a cryptographic signature to ensure data integrity
    #   We will will need this when we start logging data that we have to rely on
    #   e.g. for billing, evidence logging, safety/security critical data
    #signature = db.Column(
    #    pgtypes.TEXT
    #)


    def __init__(self,
        time_utc=None, time_mono=None,
        rcvtime_utc=None, rcvtime_mono=None,
        source_uuid=None, asset_uuid=None, rcvnode_uuid=None,
        typename=None, data=None, uuid=None
    ):

        if source_uuid in [None, '']:
            raise ValueError("Cannot create a Row object without a source_id")
        else:
            try:
                self.source_uuid = str(UUID(str(source_uuid)))
            except:
                raise ValueError("source_uuid is not a valid UUID")

        if asset_uuid in [None, '']:
            self.asset_uuid = None
        else:
            try:
                self.asset_uuid = str(UUID(str(asset_uuid)))
            except:
                raise ValueError("asset_uuid is not a valid UUID")

        if rcvnode_uuid in [None, '']:
            self.rcvnode_uuid = None
        else:
            try:
                self.rcvnode_uuid = str(UUID(str(rcvnode_uuid)))
            except:
                raise ValueError("rcvnode_uuid is not a valid UUID")

        if uuid not in [None, '']:
            self.uuid = uuid


        if typename is None:
            raise ValueError("Cannot create a Row object without a type_name given")

        #TODO: it would be nice to avoid this DB query and just handle creation of unknown types
        #  in case of an exception. But since this exception would occur during session.commit(), it
        #  might be difficult to implement it cleanly?
        #   Another workaround could be a global variable, containing a list of known types
        #  this list could be updated in case of a not listed type, then create new type if still not
        #  listed
        typequery = DataType.query.filter(DataType.typename == typename).one_or_none()
        if typequery is None:
            dt = DataType(typename, autodiscover=True)
            dt.save()

        self.typename = typename

        #FIXME: do some sanity checks on the data object - it must meet the requirements of the postgres JSONB type
        #TODO: add JSON schema validation
        self.data = data


        if time_utc is not None:
            try:
                self.time_utc = dateparser.parse(time_utc)
            except:
                raise ValueError("Cannot parse parameter time_utc with value '{}'. Must be ISO8601 / RFC3339 string".format(time_utc))

        if time_mono is not None:
            if not ((isinstance(time_mono, int) or isinstance(time_mono, float)) and time_mono > 0):
                raise ValueError("Montonic clock time must be a positive int or float value")

        if rcvtime_utc is not None:
            try:
                self.rcvtime_utc = dateparser.parse(rcvtime_utc)
            except:
                raise ValueError("Cannot parse parameter rcvtime_utc with value '{}'. Must be ISO8601 / RFC3339 string".format(rcvtime_utc))

        if rcvtime_mono is not None:
            if not ((isinstance(rcvtime_mono, int) or isinstance(rcvtime_mono, float)) and rcvtime_mono > 0):
                raise ValueError("Monotonic receive time must be a positive float or integer value")
            else:
                self.rcvtime_mono = rcvtime_mono
        else:
            self.rcvtime_mono = time.monotonic()

    def save(self):
        db.session.add(self)
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise e
