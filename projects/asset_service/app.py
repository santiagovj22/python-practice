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
from api.v1_0 import api_bp as api_v1_0_bp
from api.v2_0 import api_bp as api_v2_0_bp

logging.config.dictConfig(app_conf['logging'])


# initialize the Flask app environment
app = flask.Flask('asset_service')
app.config.update(app_conf)


# models and Database
import models
models.db.init_app(app)
migrate = flask_migrate.Migrate(app, models.db)


# activate API versions
app.register_blueprint(api_v1_0_bp)
app.register_blueprint(api_v2_0_bp)


#FIXME: this allows ALL cross-origin access. FIX IT!!!
flask_cors.CORS(app)


if __name__ == '__main__':
    app.run(debug=True, threaded=True, host='0.0.0.0', port=app.config['DEBUGSERVER_PORT'])
