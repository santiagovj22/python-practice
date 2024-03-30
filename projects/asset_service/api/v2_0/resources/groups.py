# -- groups.py --

# API endpoints for managing asset groups

# EKU Power Drives GmbH 2021, Benedikt Zier <benedikt.zier@ekupd.com>

# -- external dependencies --
from flask_restplus import Namespace, Resource, fields, marshal, abort, reqparse, inputs
from flask import current_app as app, request, redirect, url_for

from sqlalchemy import exc

# -- project dependencies --
from ..globals.pagination import paginate_with
from ..globals.uuid import UUIDField

from models.asset_group import AssetGroup, AssetGroupMembership
from models.asset import Asset


api = Namespace('Groups', description='asset groups')

class GroupLinks(fields.Raw):
    def __init__(self, **kwargs):
        fields.Raw.__init__(self, attribute='uuid', **kwargs)
        self.example = self.format('{group_uuid}')
            
    def format(self, group_uuid):
        return {'self': {'href': '/api/v2.0/groups/{}'.format(group_uuid)}} # TODO use url_for


class GroupMembershipLinks(fields.Raw):
    def __init__(self, **kwargs):
        fields.Raw.__init__(self, attribute='uuid', **kwargs)
        self.example = self.format('{group_membership_uuid}')
            
    def format(self, group_membership_uuid):
        return {'self': {'href': '/api/v2.0/groups/memberships/{}'.format(group_membership_uuid)}} # TODO use url_for

# assetclass_patch = api.model('AssetClass PATCH', {
#     'display_name': fields.String(),
#     'description': fields.String(
#         description = 'URN of the AssetClass',
#         example = 'eku:sophia:unit:frac-pump'
#     )
# })

# assetclass_put = api.inherit('AssetClass PUT', assetclass_patch, {
#     'classname': fields.String(
#         required = True
#     ),
#     'display_name': fields.String(
#         required = True
#     ),
#     'description': fields.String(
#         required = True
#     )
# })

from .assets import asset_get, asset_get_minimal

asset_group_post = api.model('AssetGroup POST', {
    'display_name': fields.String(
        description = 'AssetGroup Name to show in user interface',
        required = True,
        example = 'My Asset Group'
    ),
    'description': fields.String(
        description = ("A more detailed explanationon what this group "
            "represents and where to use it. Might be used in tooltips"),
        example = 'Represents a fleet of frac units'
    ),
    'active': fields.Boolean(
        description = 'inactive groups are hidden from the api by default'
    )
})

asset_group_get = api.inherit('AssetGroup GET', asset_group_post, {
    '_links': GroupLinks(),
    'uuid': UUIDField(
        description = 'The Group\'s unique identifier as a UUID.v4 string'
    )
})

asset_uuid_only = api.model('Asset uuid', {
    'uuid': UUIDField(required=True)
})

asset_list_patch = api.model('Asset list PATCH', {
    'append': fields.List(fields.Nested(asset_uuid_only)),
    'remove': fields.List(fields.Nested(asset_uuid_only))
})

group_membership_get = api.model('GroupMembership GET', {
    '_links': GroupMembershipLinks(),
    'uuid': UUIDField(
        description = 'The GroupMembership\'s unique identifier as a UUID.v4 string'
    ),
    'asset': fields.Nested(asset_get_minimal),
    'activation_time': fields.DateTime(
        description = 'The time the asset joined the group'
    ),
    'deactivation_time': fields.DateTime(
        description = 'The time the asset left the group'
    ),
    'active': fields.Boolean(
        description = 'Mebership is active if the asset is currently a member of the group'
    )
})

group_membership_post = api.model('GroupMembership POST', {
    'asset_uuid': UUIDField(
        description = 'The Asset\'s unique identifier as a UUID.v4 string',
        required = True
    ),
    'activation_time': fields.DateTime(
        description = 'The time the asset joined the group'
    ),
    'deactivation_time': fields.DateTime(
        description = 'The time the asset left the group'
    ),
})

timestamp_parser = reqparse.RequestParser()
timestamp_parser.add_argument('timestamp',
    type = inputs.datetime_from_iso8601,
    help = 'The timestamp at which group membership is evaluated. Example: \'2021-03-18T12:00:00\''
)

def group_from_uuid(uuid):
    try:
        group = AssetGroup.query.get(uuid)
        if group is None: raise Exception
    except: 
        abort(404, message=f'AssetGroup {uuid} doesn\'t exist')

    return group
    

@api.route('/')
class _AssetGroupList(Resource):

    @paginate_with(api,
        embedded_model = asset_group_get,
        embedded_key = 'asset_groups'
    )
    def get(self):
        
        #TODO: query = query.filter.... group state at certain time
        return AssetGroup.query

    @api.expect(asset_group_post)
    @api.marshal_with(asset_group_get)
    def post(self):
        obj = marshal(request.json, asset_group_post, skip_none=True) # This filters invalid attributes
        asset_group = AssetGroup.create(**obj)
        return asset_group


@api.route('/<uuid>')
class _AssetGroup(Resource):

    @api.marshal_with(asset_group_get)
    def get(self, uuid):
        return group_from_uuid(uuid)


@api.route('/<uuid>/assets')
class _AssetGroupAssetList(Resource):

    @paginate_with(api,
        embedded_model = asset_get,
        embedded_key = 'assets',
        embedded_mask = '{_links, title}'
    )
    @api.expect(timestamp_parser)
    def get(self, uuid):
        group = group_from_uuid(uuid)

        args = timestamp_parser.parse_args()
        timestamp = args['timestamp']

        assets = group.query_assets(timestamp=timestamp)

        return assets

    @api.expect(asset_list_patch)
    def patch(self, uuid):
        group = group_from_uuid(uuid)

        # body = marshal(request.json, asset_list_patch, skip_none=True)
        body = request.json
        appended = 0
        removed = 0

        for asset_obj in body.get('append', []):
            asset = Asset.query.get(asset_obj['uuid'])
            if asset is None:
                abort(404, message='Asset {} doesn\'t exist'.format(asset_obj['uuid']))
            try:
                group.append_asset(asset)
                appended += 1
            except Exception as e:
                print(e)
                # abort(409, message=e)

        for asset_obj in body.get('remove', []):
            asset = Asset.query.get(asset_obj['uuid'])
            if asset is None:
                abort(404, message=f'Asset {asset_obj["uuid"]} doesn\'t exist')
            try:
                group.remove_asset(asset)
                removed += 1
            except Exception as e:
                print(e)
                # abort(409, message=e)
            
        # self.get(uuid)
        return {
            'appended': appended,
            'removed': removed
        }


@api.route('/<uuid>/memberships')
class _AssetGroupMembershipList(Resource):

    @paginate_with(api,
        embedded_model = group_membership_get,
        embedded_key = 'memberships',
        embedded_mask = '{*, asset{_links, title}}'
    )
    def get(self, uuid):
        group = group_from_uuid(uuid)
        memberships = AssetGroupMembership.query.filter(AssetGroupMembership.group == group)
        return memberships

    @api.marshal_with(group_membership_get)
    @api.expect(group_membership_post)
    def post(self, uuid):
        group = group_from_uuid(uuid)

        try:
            obj = marshal(request.json, group_membership_post, skip_none=True)
            membership = AssetGroupMembership.create(group_uuid=uuid, **obj)
        except Exception as e:
            abort(400, message=e)
        
        return membership


    # @api.expect(asset_list_patch)
    # def patch(self, uuid):
    #     asset_group = AssetGroup.query.get(uuid)
    #     if asset_group is None:
    #         abort(404, message='AssetGroup {} doesn\'t exist'.format(uuid))

    #     # body = marshal(request.json, asset_list_patch, skip_none=True)
    #     body = request.json
    #     appended = 0
    #     removed = 0

    #     for asset_obj in body.get('append', []):
    #         asset = Asset.query.get(asset_obj['uuid'])
    #         if asset is None:
    #             abort(404, message='Asset {} doesn\'t exist'.format(asset_obj['uuid']))
    #         try:
    #             asset_group.append_asset(asset)
    #             appended += 1
    #         except Exception as e:
    #             print(e)
    #             # abort(409, message=e)

    #     for asset_obj in body.get('remove', []):
    #         asset = Asset.query.get(asset_obj['uuid'])
    #         if asset is None:
    #             abort(404, message='Asset {} doesn\'t exist'.format(asset_obj['uuid']))
    #         try:
    #             asset_group.remove_asset(asset)
    #             removed += 1
    #         except Exception as e:
    #             print(e)
    #             # abort(409, message=e)
            
    #     # self.get(uuid)
    #     return {
    #         'appended': appended,
    #         'removed': removed
    #     }