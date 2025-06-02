# -- activity.py --

# model describing system activities aka logging

# EKU Power Drives GmbH 2019, Kristian Binder <kristian.binder@ekupd.com>

# -- external dependencies --
from uuid import UUID, uuid4
import enum
from sqlalchemy.sql import func
import sqlalchemy.dialects.postgresql as pgtypes

# -- project dependencies --
from . import db, BaseModel

class SubjectType(enum.Enum):
    assets      = 1
    attributes  = 2
    relations   = 3
    classes     = 4
    identifiers = 5


class ActivityType(enum.Enum):
    create  = 1
    update  = 2
    delete  = 3
    enable  = 4
    disable = 5


class Activity(BaseModel):
    __tablename__ = 'activity'

    uuid = db.Column(
        pgtypes.UUID,
        server_default = db.text('uuid_generate_v4()'),
        primary_key = True
    )

    subject_type = db.Column(
        'subject_type',
        pgtypes.ENUM(SubjectType),
        nullable = False
    )

    subject_uuid = db.Column(
        'subject',
        pgtypes.UUID,
        nullable = False
        #TODO: find out if foreign key / relations to multiple tables can be done?
    )

    type = db.Column(
        'type',
        pgtypes.ENUM(ActivityType),
        nullable = False
    )

    user_uid = db.Column(
        'user',
        pgtypes.VARCHAR(100),
        nullable = False
    )

    time = db.Column(
        pgtypes.TIMESTAMP,
        nullable = False,
        server_default = db.text('NOW()')
    )

    data = db.Column(
        pgtypes.JSONB
    )
