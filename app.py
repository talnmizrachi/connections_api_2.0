from flask import Flask, request
from flask_migrate import Migrate
from flask_smorest import Api, abort
from db import db
import models
from resources.webhooks import blueprint as webhook_blueprint
from resources.connections import connections_blueprint as connections_blueprint
from resources.connections import connection_blueprint as connection_blueprint
from resources.poc_slack_ids import poc_slack_id_blueprint as poc_slack_id_blueprint
from resources.student_slack_ids import blueprint as student_slack_id_blueprint
from slack_bot import connections_blueprint_handler
from slack_bot.file_handler import blueprint as slack_event_blueprint
from cross_functions.LoggingGenerator import Logger
import os


def create_app(db_url=None):
    logger = Logger(os.path.basename(__file__).split('.')[0]).get_logger()

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

    logger.debug('Loading models')

    db.init_app(app)
    migrate = Migrate(app, db)

    api = Api(app)
    api.register_blueprint(webhook_blueprint)
    api.register_blueprint(connections_blueprint)
    api.register_blueprint(connection_blueprint)
    api.register_blueprint(poc_slack_id_blueprint)
    api.register_blueprint(student_slack_id_blueprint)
    api.register_blueprint(connections_blueprint_handler)
    api.register_blueprint(slack_event_blueprint)

    return app


if __name__ == '__main__':
    app = create_app()
    app.run()