# -- inactive.py --

# EKU Power Drives GmbH 2019, Kristian Binder <kristian.binder@ekupd.com>

# -- external dependencies --
from flask_restplus import reqparse, inputs


inactive_parser = reqparse.RequestParser()
inactive_parser.add_argument('show_inactive',
    type=inputs.boolean,
    location='args',
    default=False,
    required=False,
    help="turn on/off displaying inactive elements in result"
)
