import logging

from flask_restx import Api
from flask import Flask
from flask_cors import CORS

from config.settings import PUBLIC_KEY
from config.settings import DB_AUTH_CONNECTION
from config.settings import JWT_IDENTITY_CLAIM
from config.settings import JWT_ALGORITHM
from config.settings import JWT_DECODE_AUDIENCE

from controllers.auth_controller import init_auth_controller
from utils.auth import configure_jwt

# Init flask app
main_app = Flask(__name__)

main_app.config['JWT_PUBLIC_KEY'] = PUBLIC_KEY
main_app.config['JWT_IDENTITY_CLAIM'] = JWT_IDENTITY_CLAIM
main_app.config['JWT_ALGORITHM'] = JWT_ALGORITHM
main_app.config['JWT_DECODE_AUDIENCE'] = JWT_DECODE_AUDIENCE

# Configuration from .env
main_app.config['MONGO_URI'] = DB_AUTH_CONNECTION
main_app.config['IS_TEST'] = False

configure_jwt(main_app)

# Handling Logs
LOG_FILENAME = './logs/app.log'
logging.basicConfig(level=logging.INFO,
                    filename=LOG_FILENAME,
                    format='%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s')

main_app.logger.debug('Server running..')

# Configure service
api = Api(main_app, validate=True, title='auth service',
          description='auth service test')

# Configure cors
CORS(main_app, resources={
    r"/*": {
        "origins": "*"
    }
})

# Configure controller
init_auth_controller(main_app, api)

# Launch app local mode
if __name__ == "__main__":
    main_app.run(debug=False)
