from flask import request
from flask_smorest import Blueprint, abort
from slack_sdk import WebClient
from sqlalchemy.exc import SQLAlchemyError
from db import db
from models.poc_slack_ids import POCSlackIDsModel
from flask.views import MethodView
from cross_functions.LoggingGenerator import Logger
import os


logger = Logger(os.path.basename(__file__).split('.')[0]).get_logger()
poc_slack_id_blueprint = Blueprint("poc_slack_ids", __name__, description="actions related to POCs slack ids")


def send_welcoming_message(slack_id):
    bulbs = ":bulb::bulb::bulb:"
    opening = f"{bulbs}Thank you for joining our network of connections!{bulbs}."

    body = "What's the deal?" \
           "When a student is adding a job they are interested in to their huntr profile, I check our database for that company" \
           "if you have a listed connection there - there is a chance that you will get a message from me, and you will have 3 options - " \
           "I can send them a resume - You feel comfortable enough to send a resume of a student out" \
           "Pass - Does nothing, usefull if you know the person, but you don't feel like talking to them, you are not interested in sending a resume, or just had a bad day - we do not follow up on that at all" \
           "Connection is NOT real - you will not see that person again." \
           "If you feel comfortable enough to pass on the resumes - the student will get a notification saying that they should upload their resume to me, and I will send that to you - " \
           "The student will not have any contact with you at all." \
           "" \
           "You are not expected to do anything you are not comfortable with - your connections are your own!" \

    WebClient(token=os.environ.get("SLACK_OAUTH_TOKEN")).chat_postMessage(channel=slack_id, text=f"{opening}\n\n{body}")


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
            send_welcoming_message(data['slack_id'])
            return response, 201
        except SQLAlchemyError as e:
            logger.error(f"SQLAlchemyError - {e}")
            db.session.rollback()
            abort(500, str(e))





