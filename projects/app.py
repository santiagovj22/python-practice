# -- app.py --

# the main application run script

# EKU Power Drives GmbH 2019, Kristian Binder <kristian.binder@ekupd.com>

# -- external dependencies --
import logging
import logging.config
import flask
import flask_cors
import flask_migrate

# -- internal dependencies --
from config.app_conf import app_conf
from api.v1_1 import api_bp as api_v1_1_bp
from api.v2_0 import api_bp as api_v2_0_bp

logging.config.dictConfig(app_conf['logging'])


# initialize the Flask app environment
app = flask.Flask('data_service')
app.config.update(app_conf)

# temporary patch to ensure app can run with a config that is not
# aware of two different connections for 'legacy' and 'timescale' DBs
if app.config.get('SQLALCHEMY_BINDS') is None:
    app.config['SQLALCHEMY_BINDS'] = {}
if app.config['SQLALCHEMY_BINDS'].get('data_legacy') is None:
    app.config['SQLALCHEMY_BINDS'].update({'data_legacy': app.config.get('SQLALCHEMY_DATABASE_URI')})


# models and Database
import models
models.db.init_app(app)
#migrate = flask_migrate.Migrate(app, models.db)

with app.app_context():
    models.signal.reflectDatabase()

# activate API versions
app.register_blueprint(api_v1_1_bp, url_prefix='/api/v1.1')
app.register_blueprint(api_v2_0_bp, url_prefix='/api/v2.0')


#FIXME: this allows ALL cross-origin access. FIX IT!!!
flask_cors.CORS(app)


if __name__ == '__main__':

    app.run(debug=True, threaded=True, host='0.0.0.0', port=5001)
