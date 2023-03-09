import urllib
import requests
from datetime import datetime
from flask.views import MethodView
from flask import request
from slack_sdk import WebClient

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


def payload_parser_for_block_actions(payload_json):
	logger.info(f"payload_json:\n{payload_json}")

	if payload_json['type'] == 'block_actions':
		payload_dict_ = json.loads(payload_json['actions'][0]['value'].replace("+", " "))
		logger.debug(f"{payload_dict_['hook_id']}")
		msg_ts_ = payload_json['container']['message_ts']
		date_ = datetime.fromtimestamp(float(msg_ts_))

		return payload_dict_, date_, msg_ts_

	if payload_json['type'] == 'interactive_message':
		logger.critical(f"Payload type is interactive_message - this is the source of the error")
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
		text = f"Your connection with {payload_dict['connection_name']} from {payload_dict['company_name']} will not be considered this round, maybe next time"
	else:
		text = f":white_check_mark: Thanks for letting us know that {payload_dict['connection_name']} and you aren't really connected!"

	message = {
		"replace_original": False,
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
		payload_dict, date, msg_ts = payload_parser_for_block_actions(payload_json)
		msg_type = change_response_to_poc(payload_json, payload_dict)

		matchmaker = MatchMaker(payload_dict['hook_id'], payload_dict['company_name'], payload_dict['student_mail'], )
		matchmaker.communications_table_committer(thread_ts=msg_ts, event='MSG_FROM_POC', message_type=msg_type,
		                                          poc_name=payload_dict['poc_name'],
		                                          poc_slack_id=payload_dict['slack_id'],
		                                          approved_conn=payload_dict['connection_name'])
		# Let student know that they should send a resume to the poc
		matchmaker.define_and_send_slack_msg_for_student(msg_type, payload_dict['poc_name'], payload_dict['slack_id'])

		if msg_type == 'CONNECTION_CONFIRMED':
			def send_msg_to_sxm(student, company, poc_name):
				client = WebClient(token=os.getenv('SLACK_OAUTH_TOKEN'))
				managers = {"tal": 'U02SC4T1EBF',
				            "anisa_": "U049VQ962ER",
				            "ori_": "U030GUZ79NX"
				            }
				for manager, slack_id in managers.items():
					text = f"<@{poc_name}> confirmed that they know someone at {company} on {datetime.now().strftime('%Y-%m-%d %H:%M')} (for <@{student}>) Please check that the student saw this message (+if it was sent)"
					client.chat_postMessage(text=text, channel=slack_id)

			send_msg_to_sxm(payload_dict['slack_id'], payload_dict['company_name'],payload_dict['poc_name'] )

		if payload_dict['conn_status'] == '-1':
			matchmaker.connection_table_status_when_conn_is_rejected(payload_dict['connection_name'],
			                                                         payload_dict['poc_name'])


		# Left to do

		# move resume to POC
		# Add button for I applied
		#  # send a reminder to the poc
		# once button is clicked, send the student a message

		return payload_json, 200
