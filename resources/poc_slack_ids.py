from flask import request
from flask_smorest import Blueprint, abort
from sqlalchemy.exc import SQLAlchemyError

from db import db
from models.poc_slack_ids import POCSlackIDsModel
from flask.views import MethodView
from cross_functions.LoggingGenerator import Logger
import os


logger = Logger(os.path.basename(__file__).split('.')[0]).get_logger()
poc_slack_id_blueprint = Blueprint("poc_slack_ids", __name__, description="actions related to POCs slack ids")


@poc_slack_id_blueprint.route("/poc_slack_ids/")
class POCSlackId(MethodView):

    def post(self):
        data = request.get_json()

        poc_slack_id = POCSlackIDsModel(**data)

        try:
            logger.debug("Saving POC Slack ID")
            db.session.add(poc_slack_id)
            db.session.commit()
            response = {"status": "success", "message": "POC Slack ID saved successfully", "data": data}
            return response, 201
        except SQLAlchemyError as e:
            logger.error(f"SQLAlchemyError - {e}")
            db.session.rollback()
            abort(500, str(e))





