# -- attribute.py --

# model of an attribute, describing the properties of an asset

# EKU Power Drives GmbH 2019, Kristian Binder <kristian.binder@ekupd.com>

# -- external dependencies --
from uuid import UUID, uuid4
from sqlalchemy.sql import func
from sqlalchemy import and_
import sqlalchemy.dialects.postgresql as pgtypes

# -- project dependencies --
from . import db, BaseModel


class AttributeType(BaseModel):
    __tablename__ = 'attributetypes'

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

    # when True, an asset can only have one active attribute of this type
    # IDEA: find a way to enforce that in the DB engine with a constraint?
    unique = db.Column(
        pgtypes.BOOLEAN,
        nullable = False,
        default = True
    )

    # when True, attributes of this type will be created with the is_id flag set to True
    # IDEA: bring this logic to DB engine with a function? (since subquerys are not allowed in DEFAULT statements)
    identifier = db.Column(
        pgtypes.BOOLEAN,
        nullable = False,
        default = False,
        server_default = 'FALSE'
    )

    __mapper_args__ = {
        'polymorphic_on': identifier,
        'polymorphic_identity': False
    }

    @classmethod
    def create(cls, **kwargs):
        kwargs = {k:v for k,v in kwargs.items() if hasattr(cls, k)}
        attribute_type = cls(**kwargs)
        db.session.add(attribute_type)
        db.session.commit()
        return attribute_type

    def update(self, **kwargs):
        kwargs = {k:v for k,v in kwargs.items() if hasattr(self, k)}
        kwargs.pop('typename', None)
        for key, value in kwargs.items():
            setattr(self, key, value)
        db.session.commit()
        return self
        


class Attribute(BaseModel):
    __tablename__ = 'attributes'

    uuid = db.Column(
        pgtypes.UUID,
        server_default = db.text('uuid_generate_v4()'),
        primary_key = True

    )

    original_uuid = db.Column(
        'original',
        pgtypes.UUID,
        db.ForeignKey('attributes.uuid'),
        default = None
    )
    original = db.relationship(
        'Attribute',
        backref = db.backref('replaced_by'),
        remote_side = 'Attribute.uuid'
    )

    typename = db.Column(
        'type',
        pgtypes.VARCHAR(100),
        db.ForeignKey('attributetypes.typename'),
        nullable = False
    )

    asset_uuid = db.Column(
        'asset',
        pgtypes.UUID,
        db.ForeignKey('assets.uuid'),
        index = True,
        nullable = False
    )
    asset_active = db.relation(
        'Asset',
        backref = db.backref('attributes_active'),
        #TODO: find out how to get the Attribute.active==True in here as a dynamic parameter from the API request
        primaryjoin = "and_(Asset.uuid==Attribute.asset_uuid, Attribute.active==True)"
    )
    asset = db.relation(
        'Asset',
        backref = db.backref('attributes_all'),
        #TODO: find out how to get the Attribute.active==True in here as a dynamic parameter from the API request
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

    is_id = db.Column(
        pgtypes.BOOLEAN,
        nullable = False,
        default = False,
        server_default = 'FALSE'
    )

    __table_args__ = (
        db.Index('attributes_identifiers',
            typename, value,
            unique=True,
            postgresql_where=(and_(is_id.is_(True), active.is_(True)))
        ),
    )

    __mapper_args__ = {
        'polymorphic_on': is_id,
        'polymorphic_identity': False
    }

    @classmethod
    def create(cls, **kwargs):
        kwargs = {k:v for k,v in kwargs.items() if hasattr(cls, k)}
        attribute = cls(**kwargs)
        attribute.is_id = AttributeType.query.get(attribute.typename).identifier
        db.session.add(attribute)
        db.session.commit()
        return attribute

    def deactivate(self):
        self.active = False
        db.session.commit()
        return self

    def update(self, **kwargs):
        keys = ['typename', 'asset_uuid', 'value', 'data', 'is_id'] # properties to keep
        obj = {k:v for k,v in self.__dict__.items() if k in keys and v is not None}
        obj.update(kwargs)
        new = self.__class__(**obj)
        new.original = self
        new.active = True
        self.active = False
        db.session.add(new)
        db.session.commit()
        return new

    @property
    def asset_uuid_and_typename(self):
        return self.asset_uuid, self.typename


    #TODO: create references to log events?
