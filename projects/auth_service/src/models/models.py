from flask_restx import fields, Api

def auth_model(api: Api):
    return api.model('Auth', {'_id': fields.String, 'name': fields.String,
                              'email': fields.String, 'avatar': fields.String,
                              'hobbys': fields.List(fields.Nested(fields.String))})
