# -- uuid.py --

# uuid data type for output marshalling

# EKU Power Drives GmbH 2019, Kristian Binder <kristian.binder@ekupd.com>

# -- external dependencies --
from flask_restplus import fields


class UUIDField(fields.String):

    __schema_type__ = 'string'
    __schema_format__ = 'uuid'
    __schema_example__ = 'b6bd2396-53e4-47bf-b66d-0f369a7ab5f7'


    #TODO: add a validation function?
