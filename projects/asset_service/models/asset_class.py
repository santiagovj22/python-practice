# -- asset_class.py --

# model describing asset classes, used to group assets

# EKU Power Drives GmbH 2019, Kristian Binder <kristian.binder@ekupd.com>

# -- external dependencies --
from uuid import UUID, uuid4
from sqlalchemy.sql import func
import sqlalchemy.dialects.postgresql as pgtypes

# -- project dependencies --
from . import db, BaseModel


class AssetClass(BaseModel):
    __tablename__ = 'assetclasses'

    classname = db.Column(
        pgtypes.VARCHAR(100),
        primary_key = True
    )

    display_name = db.Column(
        pgtypes.VARCHAR(100),
        nullable = False
    )

    description = db.Column(
        pgtypes.TEXT,
        nullable = False
    )

    @classmethod
    def create(cls, **kwargs):
        kwargs = {k:v for k,v in kwargs.items() if hasattr(cls, k)}
        asset_class = cls(**kwargs)
        db.session.add(asset_class)
        db.session.commit()
        return asset_class

    def update(self, **kwargs):
        kwargs.pop('classname', None)
        for k,v in kwargs.items():
            if hasattr(self, k):
                setattr(self, k, v)
        db.session.commit()
        return self
    

class AssetClassMembership(BaseModel):
    __tablename__ = 'assetclass_members'
    __table_args__ = (
        db.UniqueConstraint('asset', 'class'),
    )

    uuid = db.Column(
        pgtypes.UUID,
        server_default = db.text('uuid_generate_v4()'),
        primary_key = True

    )

    asset_uuid = db.Column(
        'asset',
        pgtypes.UUID,
        db.ForeignKey('assets.uuid'),
        index = True,
        nullable = False
    )

    classname = db.Column(
        'class',
        pgtypes.VARCHAR(100),
        db.ForeignKey('assetclasses.classname'),
        index = True,
        nullable = False
    )

    @classmethod
    def create(cls, **kwargs):
        membership = cls(**kwargs)
        db.session.add(membership)
        db.session.commit()
        return membership

    #TODO: create references to log events?
