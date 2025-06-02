# -- asset.py --

# model of an asset

# EKU Power Drives GmbH 2019, Kristian Binder <kristian.binder@ekupd.com>

# -- external dependencies --
from uuid import UUID, uuid4
from dateutil.parser import parse as dateparse
from sqlalchemy import orm, and_, or_
from sqlalchemy.orm import exc
from sqlalchemy.sql import func
import sqlalchemy.dialects.postgresql as pgtypes

# -- project dependencies --
from . import db, BaseModel
from .activity import Activity, SubjectType, ActivityType
from .identifier import Identifier
from .asset_class import AssetClass, AssetClassMembership
from .attribute import Attribute
from .relation import Relation

class Asset(BaseModel):
    __tablename__ = 'assets'

    uuid = db.Column(
        pgtypes.UUID,
        primary_key = True,
        server_default = db.text('uuid_generate_v4()')
    )

    title = db.Column(
        pgtypes.VARCHAR(100),
        nullable = False,
    )

    summary = db.Column(
        pgtypes.TEXT
    )

    classes = db.relationship('AssetClass', secondary='assetclass_members', backref='assets')

    # groups = db.relationship('AssetGroup', secondary='asset_group_members', backref='assets') # TODO don't know how to modify behavior of relationship

    creation = db.relationship(
        'Activity',
        primaryjoin="Activity.subject_uuid == Asset.uuid",
        foreign_keys="Activity.subject_uuid",
        viewonly=True)

    #TODO: create references to log events?

    @classmethod
    def from_id(cls, identifier):
        """Try to load the asset identified by the given string
        string can be the asset UUID or an alternative identifier.
        Return None if asset not found by UUID or alt. id
        """
        asset = None
        uuid = None

        try:
            uuid = UUID(identifier)
        except:
            pass

        if isinstance(uuid, UUID):
            asset = cls.query.filter(cls.uuid == str(uuid)).one_or_none()

        if asset is None:
            asset = cls.query.join(Identifier).filter(Identifier.value == str(identifier)).one_or_none()

        return asset

    @classmethod
    def query_id(cls, identifier):

        try:
            uuid = UUID(identifier)
            query = cls.query.filter(cls.uuid == str(uuid))
        except:
            query = cls.query.join(Identifier).filter(Identifier.value == str(identifier))

        return query


    @classmethod
    def listquery(cls, filters=None):
        """returns a SQLAlchemy query object that can be used to
        retrieve the list of assets as specified by the filters.
        use the SQLAlchemy query execution methods to get a list of
        "Asset" instances.
        """
        query = cls.query
        if filters is None:
            return query

        title_contains = filters.get('title_contains')
        if title_contains is not None:
            query = query.filter(func.lower(cls.title).contains(func.lower(title_contains)))

        classes_and = filters.get('classes_and')
        classes_or = filters.get('classes_or')
        if classes_and is not None and classes_or is not None:
            raise Exception('can\'t combine parameters classes_and and classes_or')
        elif classes_and is not None:
            query = query.filter(and_(*[Asset.classes.any(AssetClassMembership.classname == name) for name in classes_and]))
        elif classes_or is not None:
            query = query.join(AssetClassMembership).filter(AssetClassMembership.classname.in_(classes_or))

        related_class = filters.get('related_class')
        if related_class is not None:
            relations_outbound = Relation.query.join(Asset, Relation.asset_src_uuid == Asset.uuid).filter(Asset.classes.any(AssetClassMembership.classname == related_class)).all()
            relations_inbound = Relation.query.join(Asset, Relation.asset_dst_uuid == Asset.uuid).filter(Asset.classes.any(AssetClassMembership.classname == related_class)).all()

            uuids = [r.asset_dst_uuid for r in relations_outbound] + [r.asset_src_uuid for r in relations_inbound]
            
            query = query.filter(Asset.uuid.in_(uuids))
        
        attribute = filters.get('attribute')
        value = filters.get('value')
        value_contains = filters.get('value_contains')
        not_none = [x is not None for x in [value, value_contains]]
        if all(not_none):
            raise Exception('can\'t combine parameters value and value_contains')
        if attribute is None and any(not_none):
            raise Exception('attribute needed for value filter')
        
        if attribute is not None:
            query = query.join(Attribute).filter(Attribute.typename == attribute, Attribute.active == True)
            # TODO if filtering for inactive attributes becomes necessary the query will result in duplicate assets and pagination breaks!!!
            if value is not None:
                query = query.filter(Attribute.value == value)
            elif value_contains is not None:
                query = query.filter(Attribute.value.contains(value_contains))

        return query.distinct() # this avoids duplicate assets matching multiple filters

    @classmethod
    def add(cls, uuid, title, summary, asset_classes):
        print('Deprecated, use create()')
        asset = cls.query.filter(cls.uuid == uuid).one_or_none()

        if asset:
            asset.title = title
            asset.summary = summary
            asset.asset_classes# = asset_classes
            db.session.update(asset)
        else:
            asset = cls()
            asset.title = title
            asset.summary = summary
            asset.asset_classes# = asset_classes
            db.session.add(asset)

        db.session.commit()

    def get_attribute(self, typename):
        # FIXME faster with query?
        print('deprecated')
        try:
            return [attr for attr in self.attributes_active if attr.typename == typename][0]
        except:
            return None

    @property
    def attributes_dict(self):
        return {attr.typename: attr for attr in self.attributes_active}

    @classmethod
    def create(cls, **kwargs):
        asset = cls(**kwargs)
        db.session.add(asset)
        db.session.commit()
        return asset

    def update(self, **kwargs):
        kwargs.pop('uuid', None)
        for k,v in kwargs.items():
            if hasattr(self, k):
                setattr(self, k, v)
        db.session.commit()
        return self

    def query_attributes(self):
        # TODO this will soon be unnecessary (endpoint inheritance)
        print('deprecated')
        return Attribute.query.filter(Attribute.asset == self).filter(Attribute.active == True)