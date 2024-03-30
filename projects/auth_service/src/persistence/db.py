import logging

from persistence.mongo_db import DatabaseConnection

DB = DatabaseConnection()

LOG = logging.getLogger('MongoDB')


def init_db(app):
    DB.init_db(app)

def get_users_collection():
    return DB.get_collection('users')