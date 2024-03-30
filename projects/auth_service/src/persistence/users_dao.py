import logging

from persistence.db import get_users_collection

LOG = logging.getLogger('Users Dao')

def user_exists(user_id):
    '''Search for user'''
    LOG.info('Verify User Registered')
    previous_user = get_users_collection().find_one({'_id': user_id})
    return previous_user is not None

def create_user(user_id, user):
    '''Create user'''
    try:
        user['_id'] = user_id
        LOG.info('Insert User into DB')
        get_users_collection().insert_one(user)
        return user
    except:
        return None