from flask_wtf import FlaskForm
from wtforms import SubmitField
from flask_wtf.file import FileField, FileRequired

class UploadForm(FlaskForm):
    photo = FileField('Selecciona imagen: ', validators = [FileRequired()])
    submit = SubmitField('Submit')

class Config(object):
    DEBUG = True
    DEVELOPMENT = True
    SECRET_KEY = 'do-i-really-need-this'
    FLASK_HTPASSWD_PATH = '/secret/.htpasswd'
    FLASK_SECRET = SECRET_KEY
    DB_HOST = 'database' # a docker link
    DB_NAME = 'DBkiero_products'
    DB_USER = 'sa'
    DB_PASS = 'qwe1234*'    