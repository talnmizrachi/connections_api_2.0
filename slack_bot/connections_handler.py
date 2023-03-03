import urllib
import requests
from datetime import datetime
from flask.views import MethodView
from flask import request
from cross_functions.LoggingGenerator import Logger
import os
from flask_smorest import Blueprint, abort
import json
import re
from slack_bot import MatchMaker

logger = Logger(os.path.basename(__file__).split('.')[0]).get_logger()
blueprint = Blueprint("connections_response", __name__, description="connection webhooks parser")


def request_parser(request_):
	poc_response = request_.get_data()
	response_time = datetime.now().isoformat()
	payload_decoded = urllib.parse.unquote(poc_response.decode())
	payload = payload_decoded.split("=")
	logger.info(f"request payload:\n{payload}")
	payload_json = json.loads("=".join(payload[1::]))

	return payload_json, response_time


def payload_parser(payload_json):
	logger.info(f"payload_json:\n{payload_json}")

	if payload_json['type'] == 'block_actions':
		payload_dict_ = json.loads(payload_json['actions'][0]['value'].replace("+", " "))

		msg_ts_ = payload_json['container']['message_ts']
		date_ = datetime.fromtimestamp(float(msg_ts_))

		return payload_dict_, date_, msg_ts_

	if payload_json['type'] == 'interactive_message':
		action_ = payload_json['actions']
		msg_ts_ = payload_json['message_ts']
		slack_id_ = payload_json['user']['id']
		timestamp_ = float(msg_ts_)
		poc_name_ = None
		company_ = payload_json['original_message']['text']

		return action_, poc_name_, company_, slack_id_, timestamp_, msg_ts_


def action_parser(action_from_payload):
	# replace this with the dictionary reader
	action_payload = action_from_payload['value'].split("|")
	contact_name_ = action_payload[0].replace('+', ' ')
	contact_status_ = action_payload[1]
	hook_id_ = action_payload[2]
	student_name_ = action_payload[3]
	student_mail_ = action_payload[4]

	return contact_name_, contact_status_, hook_id_, student_name_, student_mail_


def change_response_to_poc(payload_json, payload_dict):
	msg_type_dict = {"1": "CONNECTION_CONFIRMED", "0": "PASS", "-1": "CONNECTION_REJECTED"}
	conn_status = payload_dict['conn_status']
	if conn_status == '1':
		tadas = ":tada::tada::tada:"
		text = f"{tadas}You are Amazing!{tadas}\nWe're telling the student it's their lucky day, and that " \
		       f"they should send us the resume, so that we can forward it to you:exclamation:\nAnd don't worry " \
		       f"We'll remind you that you know {payload_dict['connection_name']} from {payload_dict['company_name']}"

	elif conn_status == '0':
		text = f"It's all good! :)"
	else:
		text = f":white_check_mark: Thanks for letting us know that {payload_dict['connection_name']} and you aren't really connected!"

	message = {
		"replace_original": True,
		"text": text
	}

	headers = {"Content-type": "application/json"}
	requests.post(payload_json['response_url'], headers=headers, data=json.dumps(message))
	return msg_type_dict[conn_status]


@blueprint.route('/connections/')
class Connection(MethodView):

	# @blueprint.arguments(PocResponseSchema)
	def post(self):
		"""

		This post request is symbolizes the willingness of a poc
		to apply on behalf of the student - which will trigger a message to
		the student.

		Once a connection is set to true - change that in the table
		if a connection is false - add next checkup date (6 months from now)
		:return:
		"""

		payload_json, response_time = request_parser(request)
		payload_dict, date, msg_ts = payload_parser(payload_json)
		msg_type = change_response_to_poc(payload_json, payload_dict)

		matchmaker = MatchMaker(payload_dict['hook_id'], payload_dict['company_name'], payload_dict['student_mail'], )
		matchmaker.communications_table_committer(thread_ts=msg_ts, event='MSG_FROM_POC', message_type=msg_type,
		                                          poc_name=payload_dict['poc_name'],
		                                          poc_slack_id=payload_dict['slack_id'],
		                                          approved_conn=payload_dict['connection_name'])
		# Let student know that they should send a resume to the poc
		msg_type = "HAVE_CONNECTIONS"
		matchmaker.define_and_send_slack_msg_for_student(msg_type, payload_dict['poc_name'], payload_dict['slack_id'])



		# Left to do
		# update false connections

		# move resume to POC + button
		#  # send a reminder to the poc
		# once button is clicked, send the student a message

		return payload_json, 200

#
# if contact_status=="-1":
#     msg_type = "CONNECTION_NOT_REAL"
# elif contact_status=="1":
#     msg_type = "CONNECTION_CONFIRMED"
# else:
#     msg_type = "CONNECTION_PASSED"
#
# commit_response_to_table(event=StaticEvents.MSG_FROM_POC,
#                          message_type=msg_type,
#                          poc=poc_name,
#                          hook_id=hook_id,
#                          msg_ts=msg_ts,
#                          company=company, slack_id=slack_id, email=None,
#                          no_of_pocs=0)
#
# tan_dict = {"-1": False, "1": True}
#
# connection = BaseConnectionModel.query.filter_by(contact_name=contact_name, poc_name=poc_name).first()
# connection.is_true_connection = tan_dict.get(contact_status)
# connection.message_ts = date
# connection.response_date = response_time
#
# try:
#     db.session.commit()
# except SQLAlchemyError as e:
#     logging.error(e)
#     db.session.rollback()
#
# if contact_status == "1":
#     # The connection is real
#     # todo - delete the other requests to the other POCs
#     communication_with_students = (CommunicationsModel
#                                    .query
#                                    .filter(CommunicationsModel.hook_id == hook_id,
#                                            CommunicationsModel.event == 'MSG_TO_STUDENT')
#                                    .first()
#                                    )
#     logging.info(f"time:\n{datetime.datetime.now()}")
#     logging.info(f"communication_with_students:\n{communication_with_students}")
#     thread_ts_to_students = communication_with_students.thread_ts
#
#     second_matchmaker = MatchMaker(hook_id,
#                                    student={"student_name": student_name,
#                                             "owner_mail": student_mail},
#                                    company=company, level=2)
#     logging.info(f"time:\n{datetime.datetime.now()}")
#     logging.info(f"second_matchmaker:\n{second_matchmaker}")
#
#     define_time = datetime.datetime.now()
#     second_matchmaker.define_student_msg(message="HAVE_CONNECTIONS")
#     logging.info(f"second_matchmaker.student_msg:\n{second_matchmaker.student_msg}")
#
#     second_matchmaker.send_msg_to_student(thread_ts=thread_ts_to_students)
#     logging.info(f"sending to student time:\n{datetime.datetime.now() - define_time}")
#
#     # second_matchmaker.send_msg_to_anisa(company, poc_name)
#
# return contact_status
