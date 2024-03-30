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
    
    'pagination': {
        'per_page_default': 200,
        'per_page_max': 2000
    },

    # cat ekupd__data_timescale1 | docker exec -i data_service_db_1 psql -U dataservice -d dataservice

    'asset_service': {
        'host': 'locahost',
        'port': 10181,
        'path': 'v1.0/',
        'auth': None
    }
}

