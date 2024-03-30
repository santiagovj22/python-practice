# -- pagination.py --

# global functions in this API version to handle pagination

# EKU Power Drives GmbH 2019, Kristian Binder <kristian.binder@ekupd.com>

# -- external dependencies --
from flask_restplus import reqparse, inputs, Model, fields, marshal
from flask_restplus.utils import merge
from flask import current_app as app, request, has_request_context
from flask_sqlalchemy import BaseQuery, Pagination
from config.app_conf import app_conf
from functools import wraps

from urllib.parse import urlencode

per_page_max = app_conf['pagination']['per_page_max']
per_page_default = app_conf['pagination']['per_page_default']

pagination_parser = reqparse.RequestParser()
pagination_parser.add_argument('page',
    type = inputs.positive,
    location = 'args',
    default = 1,
    required = False,
    help = 'pagination page number'
)
pagination_parser.add_argument('per_page',
    type = inputs.int_range(1, per_page_max),
    location = 'args',
    required = False,
    default = per_page_default,
    help = 'number of result elements to display on one page, limited to {}'.format(per_page_max)
)

def page_link(request, page):
    query = urlencode({**request.args, 'page': page}, safe=':,')
    return '{}?{}'.format(request.path, query)

class PageLink(fields.Raw):
    def __init__(self, **kwargs):
        fields.Raw.__init__(self, **kwargs)
        self.example = {'href': '/some/url?page=2'}
    
    def format(self, page):
        if has_request_context():
            return {'href': page_link(request, page)}

class SelfLink(fields.Raw):
    def __init__(self, **kwargs):
        fields.Raw.__init__(self, **kwargs)
        self.example = {'href': '/some/url'}
        self.description = 'URL to this resource'
    
    def format(self, value):
        if has_request_context():
            return {'href': request.full_path}


def add_pagination_model(api, embedded_model, embedded_key, embedded_mask=None):
    
    name = embedded_model.name + ' pagination'

    pagniation_links = api.model(name + ' links', {
            'self': SelfLink(default=True), # if no default is given, field is not rendered
            'next': PageLink(attribute='next_num'),
            'prev': PageLink(attribute='prev_num')
            # TODO implement first and last?
        }
    )
    
    embedded_list = api.model(
        'List of {}'.format(embedded_model.name),
        {embedded_key: fields.List(fields.Nested(embedded_model),
            attribute = 'items',
            description = 'list of {}'.format(embedded_model.name)
        )}
    )

    mask = None
    if embedded_mask is not None:
        mask = '{*, _embedded{' + embedded_key + embedded_mask + '}}'
    
    pagination_model = api.model(name, {
        '_total': fields.Integer(
            attribute = 'pagination.total',
            description = 'total number of results'
        ),
        '_links': fields.Nested(pagniation_links,
            attribute = 'pagination',
            description = 'related links',
            skip_none = True # this hides the 'next' or 'prev' links if they don't exist
        ),
        # attribute could be '__dict__' if the given object is the pagination and not {'pagination': pagination} but this doesn't work for property methods like 'next_num'
        '_embedded': fields.Nested(embedded_list,
            attribute = 'pagination',
            description = 'embedded information'
        )
    }, mask = mask)

    return pagination_model

def paginate_list(items, page, per_page):
    total = len(items)
    start = (page - 1) * per_page
    end = start + per_page
    page_items = items[start:end]
    return Pagination(None, page, per_page, total, page_items)

def paginate_with(api=None, **kwargs):
    """A decorator that accepts a query object and returns a json pagination object.
    Always place this decorator above all others as this is necessary to extend the documentation correctly.
    """
    def decorator(func):
        fields = add_pagination_model(api=api, **kwargs)
        
        # Copy what 'marshal_with' decorator does to add the pagination and model masks to the api doc
        doc = {
            'responses': {200: (fields.name, fields)},
            '__mask__': True if fields.__mask__ is None else str(fields.__mask__),
        }
        func.__apidoc__ = merge(getattr(func, '__apidoc__', {}), doc)
        if func.__apidoc__.get('expect') is None:
            func.__apidoc__['expect'] = [pagination_parser]
        else:
            func.__apidoc__['expect'][0].args.extend(pagination_parser.args)
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            expand = inputs.boolean(request.args.get('expand', False))
            mask = '*' if expand else request.headers.get(app.config['RESTPLUS_MASK_HEADER']) # If expand is true the '*' mask shows all fields. Else use the mask given in the header. If no mask is given in header it defaults to None.
            pagination_args = pagination_parser.parse_args()

            res = func(*args, **kwargs)

            if isinstance(res, BaseQuery):
                pagination = res.paginate(**pagination_args)
            elif isinstance(res, list):
                pagination = paginate_list(res, **pagination_args)
            else:
                raise Exception('Unsupported type for pagination, must be list or BaseQuery')
            
            return marshal({'pagination': pagination}, fields, mask=mask) # If mask is None, the default mask of the embedded pagination model is used
        return wrapper
    return decorator