import threading
import os
from datetime import datetime

from dotenv import load_dotenv
from flask import request, make_response
from flask.views import MethodView
from flask_smorest import Blueprint
from slack_sdk import WebClient
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker
from models import CommunicationsModel, WebhooksModel
from schemas import SlackEventSchema
from cross_functions.LoggingGenerator import Logger

load_dotenv()
logger = Logger(os.path.basename(__file__).split('.')[0]).get_logger()

blueprint = Blueprint("slack_events", __name__, description="slack events parser")


def create_text_for_poc(company, approved_connection, job_title, link_to_cv):
	txt = f"""Hey, Here is the CV for the *{job_title[0]}* position in *{company}*, for your connection *{approved_connection}*
<{link_to_cv}|The student's CV>, Please update us if you forwarded this CV to your connections (so that we can let the student know 
it's ok."""
	return txt


def send_msg_to_sxm(client, student, company, poc_name):
	managers = {"tal": 'U02SC4T1EBF',
	            "anisa_": "U049VQ962ER",
	            "ori_": "U030GUZ79NX"
	            }
	for manager, slack_id in managers.items():
		text = f"<@{student}> sent their resumes to {poc_name} that knows someone at {company} on {datetime.now().strftime('%Y-%m-%d %H:%M')}"
		client.chat_postMessage(text=text, channel=slack_id)


def interim_slack_handler(file_id, user_id, file_token):
	client = WebClient(token=os.getenv('SLACK_OAUTH_TOKEN'))
	file_data = client.files_info(file=file_id).data['file']
	file_name = file_data['name']
	file_link = file_data['permalink']
	thread_ts = list(file_data['shares']['private'].values())[0][0]['thread_ts']
	session_ = session_generator()
	hook_id, company, student_mail, full_name = (session_.
	                                             query(CommunicationsModel).
	                                             with_entities(CommunicationsModel.hook_id,
	                                                           CommunicationsModel.company,
	                                                           CommunicationsModel.student_email,
	                                                           CommunicationsModel.full_name
	                                                           ).
	                                             filter_by(student_slack_id=user_id, thread_ts=thread_ts)
	                                             .first()
	                                             )
	logger.debug(f"{hook_id} -Interim Slack Handler")
	poc_name, poc_slack_id, connection_name = (session_.
	                                           query(CommunicationsModel).
	                                           with_entities(CommunicationsModel.poc_name,
	                                                         CommunicationsModel.poc_slack_id,
	                                                         CommunicationsModel.approved_connection_name
	                                                         ).
	                                           filter_by(hook_id=hook_id, message_type='CONNECTION_CONFIRMED')
	                                           .first()
	                                           )
	logger.debug(f"{hook_id} - getting information for the poc")
	new_communications = CommunicationsModel(hook_id=hook_id, thread_ts=thread_ts, event="MSG_FROM_STUDENT",
	                                         message_type="STUDENT_SENT_CV", company=company,
	                                         student_email=student_mail, full_name=full_name, cv_link=file_link,
	                                         file_name=file_name, student_slack_id=user_id, slack_file_token=file_token,
	                                         poc_name=poc_name, poc_slack_id=poc_slack_id, job_id=None)

	try:
		logger.debug(f"{hook_id} -Adding the new communication to the database")
		session_.add(new_communications)
		session_.commit()
		logger.debug(f"Added new communication:\t{new_communications}")
	except SQLAlchemyError as e:
		session_.rollback()
		logger.error(f"Failed to add new communication:\t{new_communications}")
		logger.error(e)
	logger.debug(f"{hook_id} -Getting the job title")

	job_title = (session_.
	             query(WebhooksModel).
	             with_entities(WebhooksModel.job_title).
	             filter_by(hook_id=hook_id).
	             first()
	             )

	client.chat_postMessage(channel=poc_slack_id,
	                        text=create_text_for_poc(company, connection_name, job_title, file_link))

	send_msg_to_sxm(client, user_id, company, poc_name)

	new_communications = CommunicationsModel(hook_id=hook_id, thread_ts=thread_ts, event="MSG_TO_POC",
	                                         message_type="ASTRID_FORWARDED_TO_POC", company=company,
	                                         student_email=student_mail, full_name=full_name, cv_link=file_link,
	                                         file_name=file_name, student_slack_id=user_id, slack_file_token=file_token,
	                                         poc_name=poc_name, poc_slack_id=poc_slack_id,
	                                         approved_connection_name=connection_name, job_id=None)
	try:
		session_.add(new_communications)
		session_.commit()
		logger.debug(f"Added new communication:\t{new_communications}")
	except SQLAlchemyError as e:
		session_.rollback()
		logger.error(f"Failed to add new communication:\t{new_communications}")
		logger.error(e)


# return matchmaker


def session_generator():
	engine = create_engine(os.environ["DATABASE_URL"])
	session_maker = sessionmaker(bind=engine)
	session_ = session_maker()

	return session_


def main_file_sender(data):
	event = data.get("event")
	file = event['file']
	file_id = file["id"]
	user_id = event.get("user_id")
	event_ts = event.get("event_ts")
	file_token = data['token']

	logger.debug(f"Received event:\t{event}")
	logger.debug(f"Received file_id:\t{file_id}")

	matchmaker = interim_slack_handler(file_id, user_id, file_token)


@blueprint.route("/slack_events/")
class SlackEventCatcher(MethodView):

	@blueprint.response(200, SlackEventSchema)
	def post(self):

		data = request.get_json()
		logger.info(f"file_handler_data:\n{data}")

		if 'challenge' in data:
			logger.debug(f"challenge_data:\n{data}")
			return {'challenge': data['challenge']}

		else:
			logger.debug(f"{__name__}_running")
			make_response("", 200)

			code_breaker = threading.Thread(target=main_file_sender, args=(data,))
			code_breaker.start()


#

if __name__ == '__main__':
	session = session_generator()
	details = (session.
	           query(CommunicationsModel).
	           with_entities(CommunicationsModel.hook_id,
	                         CommunicationsModel.company,
	                         CommunicationsModel.poc_name,
	                         CommunicationsModel.event,
	                         CommunicationsModel.thread_ts,
	                         CommunicationsModel.message_type,
	                         CommunicationsModel.student_email).
	           filter_by(student_slack_id='U02SC4T1EBF',
	                     # thread_ts=event_ts,
	                     )
	           .all()
	           )
	print([d for d in details if d[4] == '1677838936.286059'])
	print(f"Collected all the details:\t{details}")
