# -- app_conf.example.py --

# application configuration object example
#
# this is an example configuration object. Please copy to a new file named
# app_conf.py residing in the same directory.
# app_conf.py will not be tracked by git versioning.

# EKU Power Drives GmbH 2019, Kristian Binder <kristian.binder@ekupd.com>

import os
import logging

app_conf = {
    'logging': {
        'version': 1,
        'formatters': {
            'default': {
                'format': '{asctime} [{levelname}] by [{name}]: {message}',
                'datefmt': '%Y-%m-%d %H:%M:%S',
                'style': '{'
            }
        },
        'handlers': {
            'stderr': {
                'class': 'logging.StreamHandler',
                'formatter': 'default',
                'stream': 'ext://sys.stderr',
                'level': logging.DEBUG
            }
        },
        'loggers': {
            #TODO: work with specific loggers instead of using root logger for everything
        },
        'root': {
            'level': logging.DEBUG,
            'handlers': ['stderr']
        }
    },

    'SQLALCHEMY_DATABASE_URI': "postgres://dataservice:data@localhost/dataservice",
    'SQLALCHEMY_TRACK_MODIFICATIONS': False,
    'SQLALCHEMY_BINDS': {
        'data_legacy': "postgres://user:pass@host/database"
    },

    'pagination': {
        'per_page_default': 200,
        'per_page_max': 2000
    },

    'asset_service': {
        'host': 'locahost',
        'port': 10181,
        'path': 'v1.0/',
        'auth': None
    }
}
