# -- asset_group.py --

# model describing asset groups, used to group assets

# EKU Power Drives GmbH 2021, Benedikt Zier <benedikt.zier@ekupd.com>

# -- external dependencies --
from uuid import UUID, uuid4
import sqlalchemy.dialects.postgresql as pgtypes
from datetime import datetime

# -- project dependencies --
from . import db, BaseModel
from .asset import Asset


class AssetGroup(BaseModel):
    __tablename__ = 'asset_groups'

    uuid = db.Column(
        pgtypes.UUID,
        primary_key = True,
        server_default = db.text('uuid_generate_v4()')
    )

    display_name = db.Column(
        pgtypes.VARCHAR(100),
        nullable = False
    )

    description = db.Column(
        pgtypes.TEXT,
    )

    active = db.Column (
        pgtypes.BOOLEAN,
        default = True
    )

    @classmethod
    def create(cls, **kwargs):
        kwargs = {k:v for k,v in kwargs.items() if hasattr(cls, k)}
        asset_group = cls(**kwargs)
        db.session.add(asset_group)
        db.session.commit()
        return asset_group

    def update(self, **kwargs):
        for k,v in kwargs.items():
            if hasattr(self, k):
                setattr(self, k, v)
        db.session.commit()
        return self

    def query_assets(self, timestamp=None):
        query = Asset.query.join(AssetGroupMembership).filter(AssetGroupMembership.group == self)
        if timestamp is None:
            return query.filter(AssetGroupMembership.active == True)
        else:
            return query.filter(AssetGroupMembership.activation_time <= timestamp).filter(AssetGroupMembership.deactivation_time >= timestamp)

    def append_asset(self, asset):
        # check if the asset is allreay a group member
        if AssetGroupMembership.query.filter(AssetGroupMembership.group == self).filter(AssetGroupMembership.asset == asset).filter(AssetGroupMembership.active == True).one_or_none():
            raise Exception(f'Asset {asset.uuid} is already in this group')
        membership = AssetGroupMembership(group_uuid=self.uuid, asset_uuid=asset.uuid, activation_time=datetime.utcnow())
        db.session.add(membership)
        db.session.commit()

    def remove_asset(self, asset):
        # check if the asset has an active membership
        membership = AssetGroupMembership.query.filter(AssetGroupMembership.group == self).filter(AssetGroupMembership.asset == asset).filter(AssetGroupMembership.active == True).one_or_none()
        if membership is None:
            raise Exception(f'Asset {asset.uuid} is not in this group')
        membership.deactivate()

class AssetGroupMembership(BaseModel):
    __tablename__ = 'asset_group_members'
    # __table_args__ = (
    #     db.UniqueConstraint('asset', 'group'),
    # ) # asset can have multiple memberships in one group, their timeframe mustn't overlap

    uuid = db.Column(
        pgtypes.UUID,
        server_default = db.text('uuid_generate_v4()'),
        primary_key = True
    )

    asset_uuid = db.Column(
        pgtypes.UUID,
        db.ForeignKey('assets.uuid'),
        index = True,
        nullable = False
    )

    asset = db.relation(
        'Asset',
        backref = db.backref('asset_group_memberships')
        # primaryjoin = "and_(Asset.uuid==Attribute.asset_uuid, Attribute.active==True)"
    )

    group_uuid = db.Column(
        pgtypes.UUID,
        db.ForeignKey('asset_groups.uuid'),
        index = True,
        nullable = False
    )

    group = db.relation(
        'AssetGroup',
        backref = db.backref('memberships')
        # primaryjoin = "and_(Asset.uuid==Attribute.asset_uuid, Attribute.active==True)"
    )

    activation_time = db.Column(
        pgtypes.TIMESTAMP,
        nullable = False,
        server_default = db.text('(now() at time zone \'utc\')')
    )

    deactivation_time = db.Column(
        pgtypes.TIMESTAMP
    )

    active = db.Column (
        pgtypes.BOOLEAN,
        default = True
    )

    @classmethod
    def create(cls, group_uuid, asset_uuid, activation_time=datetime.utcnow(), deactivation_time=None):
        # check if the asset is allreay a group member
        if cls.query\
            .filter(cls.group_uuid == group_uuid)\
            .filter(cls.asset_uuid == asset_uuid)\
            .filter(cls.active == True)\
            .one_or_none():
                raise Exception(f'Asset {asset_uuid} is already in this group')

        if isinstance(activation_time, str):
            activation_time = datetime.strptime(activation_time, '%Y-%m-%dT%H:%M:%S')
        if isinstance(deactivation_time, str):
            deactivation_time = datetime.strptime(deactivation_time, '%Y-%m-%dT%H:%M:%S')
        if deactivation_time is None:
            active = True
        else:
            if deactivation_time <= activation_time:
                raise Exception('deactivation_time must be after activation_time')
            elif deactivation_time > datetime.utcnow():
                raise Exception('deactivation_time can\'t be in the future')
            active = False

        membership = cls(
            asset_uuid = asset_uuid,
            group_uuid = group_uuid,
            activation_time = activation_time,
            deactivation_time = deactivation_time,
            active = active
        )
        db.session.add(membership)
        db.session.commit()
        return membership

    def deactivate(self):
        if not self.active:
            raise Exception('membership is inactive')
        self.deactivation_time = datetime.utcnow()
        self.active = False
        db.session.commit()
    