# -- pagination.py --

# global functions in this API version to handle pagination

# EKU Power Drives GmbH 2019, Kristian Binder <kristian.binder@ekupd.com>

# -- external dependencies --
from flask_restplus import reqparse, inputs
from flask import current_app as app



pagination_parser = reqparse.RequestParser()
pagination_parser.add_argument('page_no',
    type=inputs.natural,
    location='args',
    default=1,
    required=False,
    help="pagination page number"
)
pagination_parser.add_argument('page_size',
    type=inputs.natural,
    location='args',
    required=False,
    help="number of result elements to display on one page"
)
