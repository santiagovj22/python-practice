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

    'SQLALCHEMY_DATABASE_URI': "postgres://assetservice:asset@localhost/assetservice",
    'SQLALCHEMY_TRACK_MODIFICATIONS': False,

    'pagination': {
        'per_page_default': 200,
        'per_page_max': 2000
    },

    'data_service': {
        'host': 'locahost',
        'port': 10182,
        'path': 'v1.1/',
        'auth': None
    },

    'asset_sync': [
        {
            'tenant':'{%TENANT%}',
            'user':'{%NODETN%}@fatnode',
            'secret':'{%HOSTPW%}',
            'source_node':'{%CLOUDURL%}'
        }
    ]
}
