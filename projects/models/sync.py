# -- sync.py --

# model of a synchronization run

# EKU Power Drives GmbH 2019, Kristian Binder <kristian.binder@ekupd.com>

# -- external dependencies --
from uuid import UUID, uuid4
from sqlalchemy.sql import func
import sqlalchemy.dialects.postgresql as pgtypes

# -- project dependencies --
from . import db, BaseModel
from .row import Row
from .datatype import DataType


class Sync(BaseModel):

    __bind_key__ = 'data_legacy'
    __tablename__ = 'sync'

    uuid = db.Column(
        pgtypes.UUID,
        primary_key = True,
        server_default = db.text('uuid_generate_v4()')
    )

    row_uuid = db.Column(
        'row',
        pgtypes.UUID,
        db.ForeignKey('data.uuid'),
        nullable = False
    )

    row = db.relationship(
        'Row',
        backref = db.backref('syncs', lazy = True)
    )

    time_utc = db.Column(
        pgtypes.TIMESTAMP
    )

    host = db.Column(
        pgtypes.TEXT,
        nullable = False
    )

    result = db.Column(
        pgtypes.JSONB
    )


    @classmethod
    def get_row_syncs(cls, row_uuid):
        q = cls.query.filter(cls.row_uuid == row_uuid)
        return q.all()
