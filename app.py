from flask import Flask, request
from flask_smorest import abort
from cross_functions.LoggingGenerator import Logger
import os


def create_app(db_url=None):
    logger = Logger("app.py").get_logger()
    app = Flask(__name__)

    logger.debug('Loading environment variables')

    app.config["PROPAGATE_EXCEPTIONS"] = True
    app.config["JSONIFY_PRETTYPRINT_REGULAR"] = True
    app.config["API_TITLE"] = "Stores REST Api"
    app.config["API_VERSION"] = "v1"
    app.config["OPENAPI_VERSION"] = "3.0.3"
    app.config["OPENAPI_URL_PREFIX"] = "/"
    app.config["OPENAPI_SWAGGER_UI_PATH"] = "/swagger-ui"
    app.config["OPENAPI_SWAGGER_UI_URL"] = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url or os.getenv("DATABASE_URL", 'sqlite:///data.db')
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    @app.get('/')
    def get_index():
        return "Hello World!"

    return app



if __name__ == '__main__':
    app = create_app()
    app.run()