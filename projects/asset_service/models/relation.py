# -- relation.py --

# model of a relation, describing connections between assets

# EKU Power Drives GmbH 2019, Kristian Binder <kristian.binder@ekupd.com>

# -- external dependencies --
from uuid import UUID, uuid4
from sqlalchemy.sql import func
import sqlalchemy.dialects.postgresql as pgtypes

# -- project dependencies --
from . import db, BaseModel


class RelationType(BaseModel):
    __tablename__ = 'relationtypes'

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

    unique_src = db.Column(
        pgtypes.BOOLEAN,
        nullable = False,
        default = False
    )

    unique_dst = db.Column(
        pgtypes.BOOLEAN,
        nullable = False,
        default = False
    )


class Relation(BaseModel):
    __tablename__ = 'relations'
    __table_args__ = (
        db.CheckConstraint('asset_src != asset_dst'), #TODO: check if it really works...
    )

    uuid = db.Column(
        pgtypes.UUID,
        server_default = db.text('uuid_generate_v4()'),
        primary_key = True

    )

    original_uuid = db.Column(
        'original',
        pgtypes.UUID,
        db.ForeignKey('relations.uuid'),
        default = None
    )
    original = db.relationship(
        'Relation',
        backref = db.backref('replaced_by'),
        remote_side = 'Relation.uuid'
    )

    typename = db.Column(
        'type',
        pgtypes.VARCHAR(100),
        db.ForeignKey('relationtypes.typename'),
        nullable = False
    )
    type = db.relation(
        'RelationType',
        backref = db.backref('relations')
    )

    asset_src_uuid = db.Column(
        'asset_src',
        pgtypes.UUID,
        db.ForeignKey('assets.uuid'),
        index = True,
        nullable = False
    )
    asset_src_active = db.relation(
        'Asset',
        foreign_keys = [asset_src_uuid],
        backref = db.backref('relations_outbound_active'),
        #TODO: find out how to get the Relation.active==True in here as a dynamic parameter from the API request
        primaryjoin = "and_(Asset.uuid==Relation.asset_src_uuid, Relation.active==True)"
    )
    asset_src = db.relation(
        'Asset',
        foreign_keys = [asset_src_uuid],
        backref = db.backref('relations_outbound_all'),
        #TODO: find out how to get the Relation.active==True in here as a dynamic parameter from the API request
    )

    asset_dst_uuid = db.Column(
        'asset_dst',
        pgtypes.UUID,
        db.ForeignKey('assets.uuid'),
        index = True,
        nullable = False
    )
    asset_dst_active = db.relation(
        'Asset',
        foreign_keys = [asset_dst_uuid],
        backref = db.backref('relations_inbound_active'),
        #TODO: find out how to get the Relation.active==True in here as a dynamic parameter from the API request
        primaryjoin = "and_(Asset.uuid==Relation.asset_dst_uuid, Relation.active==True)"
    )
    asset_dst = db.relation(
        'Asset',
        foreign_keys = [asset_dst_uuid],
        backref = db.backref('relations_inbound_all'),
        #TODO: find out how to get the Relation.active==True in here as a dynamic parameter from the API request
    )

    value = db.Column(
        pgtypes.TEXT
    )

    data = db.Column(
        pgtypes.JSONB
    )

    active = db.Column (
        pgtypes.BOOLEAN
    )


    #TODO: create references to log events?
