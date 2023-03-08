import os
from datetime import datetime

from flask import abort
from sqlalchemy.exc import SQLAlchemyError
from models import POCSlackIDsModel, CommunicationsModel, StudentSlackIDsModel, ConnectionModel
from cross_functions.LoggingGenerator import Logger
from slack_bot.slack_msg_templates import main as slack_poc_template
from db import db
import pandas as pd
from slack_sdk import WebClient
from dotenv import load_dotenv
import random

logger = Logger(os.path.basename(__file__).split('.')[0]).get_logger()
load_dotenv()


class MatchMaker:

	def __init__(self, hook_id, company, student_mail):
		self.student_main_thread = None
		self.student_thread_ts = None
		self.poc_to_slack_id_mapping = None
		self.hook_id = hook_id
		self.slack_client = WebClient(token=os.getenv("SLACK_OAUTH_TOKEN"))
		self.company = company
		self.student_mail = student_mail
		self.slack_msg = None
		self.slack_msg_id = None
		self.slack_msg_ts = None
		self.thread_ts = None
		self.event = None
		self.message_type = None
		self.cv_link = None
		self.file_name = None
		self.student_name = None
		self.student_slack_id = None
		self.poc_name = None
		self.poc_slack_id = None
		self.poc_approved_name_of_connection = None
		self.slack_file_token = None
		self.connections = None
		self.possible_connection_for_a_match = pd.DataFrame()
		self.poc_slack_msgs_dict = {}
		self.student_msg = ""

		logger.debug(f"{self.hook_id} - Initializing MatchMaker")

	def connection_table_status_when_conn_is_rejected(self, contact_name, poc_name):
		logger.debug(f"{self.hook_id} - updating Connection table status when conn is rejected")

		connection = (ConnectionModel.
		              query.
		              filter_by(contact_name=contact_name,
		                        poc_name=poc_name,
		                        company_name=self.company)
		              .first()
		              )
		connection.is_true_connection = False
		connection.response_date = datetime.now()

		try:
			logger.debug(f"what_to_commit:\t{connection}")
			db.session.add(connection)
			db.session.commit()
		except SQLAlchemyError as e:
			db.session.rollback()
			logger.error(f"SQLAlchemyError - {e}")
			abort(500, str(e))

	def communications_table_committer(self, thread_ts, event, message_type, cv_link = None,
	                                   file_name = None, poc_name = None, poc_slack_id = None,
	                                   slack_file_token = None, approved_conn = None):
		logger.debug(f"{self.hook_id} - Building Commit communications from MatchMaker")
		if self.student_slack_id is None:
			self.student_data_from_mail_setter()

		columns = {
			"hook_id": self.hook_id,
			'thread_ts': thread_ts,
			'event': event,
			'message_type': message_type,
			'company': self.company,
			'cv_link': cv_link,
			'file_name': file_name,
			'full_name': self.student_name,
			'student_slack_id': self.student_slack_id,
			'student_email': self.student_mail,
			'poc_name': poc_name,
			'poc_slack_id': poc_slack_id,
			'slack_file_token': slack_file_token,
			"approved_connection_name": approved_conn
		}

		coms = CommunicationsModel(**columns)
		try:
			logger.debug(f"{self.hook_id} - Committing communications table from MatchMaker")
			db.session.add(coms)
			db.session.commit()
		except SQLAlchemyError as e:
			db.session.rollback()
			logger.error(f"SQLAlchemyError - {e}")
			abort(500, str(e))

	def student_name_setter(self, student_name):
		logger.debug(f"{self.hook_id} - Setting student name")
		self.student_name = student_name

	def connections_setter(self, connections):
		logger.debug(f"{self.hook_id} - Setting connections")
		self.connections = connections

	def student_data_from_mail_setter(self):
		logger.debug(f"{self.hook_id} - Setting student name and slack id")
		details = (StudentSlackIDsModel
		           .query
		           .with_entities(StudentSlackIDsModel.student_name, StudentSlackIDsModel.slack_id)
		           .filter(StudentSlackIDsModel.student_email == self.student_mail)
		           .first()
		           )

		self.student_name = details[0]
		self.student_slack_id = details[1]

	def possible_connection_for_a_match_setter(self):
		possible_connections = pd.DataFrame(self.connections, columns=["contact_name", "poc_name"])

		if possible_connections['poc_name'].nunique() > 3:
			# randomize the number of pocs that are getting matched
			names = random.sample(list(possible_connections['poc_name'].unique()), k=3)
			self.possible_connection_for_a_match = possible_connections[possible_connections['poc_name'].isin(names)].copy()
			logger.debug(f"connections picked randomly:{self.possible_connection_for_a_match}")
			return None

		self.possible_connection_for_a_match = possible_connections

	def create_poc_to_slack_id_mapping(self):
		logger.debug(f"START")
		self.possible_connection_for_a_match_setter()
		var = (POCSlackIDsModel
		       .query
		       .with_entities(POCSlackIDsModel.poc_name, POCSlackIDsModel.slack_id)
		       .filter(POCSlackIDsModel.poc_name.in_(self.possible_connection_for_a_match['poc_name'].unique()))
		       .all()
		       )
		self.poc_to_slack_id_mapping = dict(var)
		logger.debug(f"self.poc_to_slack_id_mapping:\t{self.poc_to_slack_id_mapping}")

	def send_msgs_to_pocs_to_check_if_connections_are_real(self, job_url, email, message_type):

		logger.debug(f"{self.hook_id} - creating poc_to_slack_id_mapping")
		self.create_poc_to_slack_id_mapping()


		pocs_dict = {}

		for poc in self.possible_connection_for_a_match['poc_name'].unique():
			logger.debug(f"Building block for poc: {poc}")
			temp = (self.possible_connection_for_a_match[
				        (self.possible_connection_for_a_match['poc_name'] == poc)
			        ].copy())
			temp = temp.sample(min(3, len(temp)))
			temp = temp.sort_index()
			slack_id = self.poc_to_slack_id_mapping.get(poc)
			if slack_id is None:
				logger.error(f"Could not find slack_id for poc: {poc}")
				self.slack_client.chat_postMessage(channel='U02SC4T1EBF',  # C04SG7ZQNS0
				                                   text=f"Could not find slack_id for poc: {poc}")
				continue
			temp_blocks = slack_poc_template(poc,
			                                 self.company,
			                                 temp['contact_name'].unique(),
			                                 self.hook_id,
			                                 self.student_name,
			                                 email, job_url, slack_id)

			pocs_dict[poc] = {"slack_id": slack_id, "blocks": [temp_blocks]}
			response = self.slack_client.chat_postMessage(channel=slack_id,
			                                              text="Help our students find the best match!",
			                                              blocks=temp_blocks['blocks']
			                                              )

			self.communications_table_committer(response.get('ts'), "MSG_TO_POC", message_type,
			                                    poc_name=poc,
			                                    poc_slack_id=slack_id)

	def define_and_send_slack_msg_for_poc(self, message_type, job_url, email):
		"""
		Cases -
		1. Is the connection real
		2. here is the cv
		3. reminder to apply
		3. did you apply on their behalf?

		:return:
		"""
		logger.debug(f"{self.hook_id} - Building slack msg for poc (message_type={message_type})")

		if self.student_slack_id is None:
			self.student_data_from_mail_setter()

		if message_type == 'CHECKING_STATE_OF_CONNECTIONS':
			# {"poc_name": {"poc_slack_id_key": "poc_slack_id_value", "blocks": []}}
			self.send_msgs_to_pocs_to_check_if_connections_are_real(job_url=job_url, email=email,
			                                                        message_type=message_type)

		elif message_type == 'ASTRID_FORWARDED_TO_POC':
			# Right now, not needed - sending it inside the code
			...
		else:
			logger.warning(f"{self.hook_id} - NOT YET IMPLEMENTED")

	def define_slack_msg_for_student(self, message_type):
		"""
		Cases -
		we don't have connections at all for the student
		we have connection(s) for a match

		:return:
		"""
		logger.debug(f"{self.hook_id} - Building slack msg for student (message_type={message_type})")
		if self.possible_connection_for_a_match is None:
			self.possible_connection_for_a_match_setter()

		if message_type == "CONNECTION_CONFIRMED":
			self.student_msg = f"Hey {self.student_name}! We have a connection to *{self.company}* for you!, please " \
			                   f"send me you TAILORED resume me (just upload the file in this thread)"

			return self.student_msg

		elif message_type == "NO_CONNECTIONS":
			self.student_msg = f"Hey {self.student_name}, looks like we don't have any " \
			                   f"connections in *{self.company}* right now" \
			                   f"\nTailor your resume and apply via company's website"

		elif message_type == "CHECKING_CONNECTIONS_WITH_POCS":

			self.student_msg = f"Hey {self.student_name}, We might have connection(s) from in *{self.company}*." \
			                   f"\nI'll now send a message to those contacts and check if their " \
			                   f"connections are real and if they feel comfortable with applying on your behalf. " \
			                   f"\n\nIn the meanwhile, start tailoring your resume to the position" \
			                   f" - see what matters most and make sure it stands out."

		else:
			logger.warning(f"{self.hook_id} - NOT YET IMPLEMENTED: message_type={message_type}")

	def define_and_send_slack_msg_for_student(self, message_type, *args):
		logger.debug(f"{self.hook_id} - defining and sending slack msg for student (message_type={message_type})")

		if self.student_slack_id is None:
			self.student_data_from_mail_setter()
		self.define_slack_msg_for_student(message_type)

		if message_type in ["NO_CONNECTIONS", "CHECKING_CONNECTIONS_WITH_POCS"]:
			resp = self.slack_client.chat_postMessage(text=self.student_msg,
			                                          channel=self.student_slack_id)
			self.student_main_thread = resp.get('ts')
			self.communications_table_committer(self.student_main_thread, "MSG_TO_STUDENT", message_type)

		if message_type in ["HAVE_CONNECTIONS", 'CONNECTION_CONFIRMED']:
			self.student_thread_ts_getter()
			self.slack_client.chat_postMessage(text=self.student_msg,
			                                   channel=self.student_slack_id,
			                                   thread_ts=self.thread_ts)
			self.communications_table_committer(self.student_main_thread, "MSG_TO_STUDENT", "REQUEST_FOR_CV",
			                                    poc_name=args[0],
			                                    poc_slack_id=args[1])

		if message_type in ("PASS", ):
			self.student_thread_ts_getter()


		return self.student_msg

	def student_thread_ts_getter(self):
		logger.debug(f"{self.hook_id} - getting thread_ts for student: {self.student_slack_id}")
		self.thread_ts = (CommunicationsModel.
		                  query.
		                  with_entities(CommunicationsModel.thread_ts).
		                  filter(CommunicationsModel.event == "MSG_TO_STUDENT",
		                         CommunicationsModel.hook_id == self.hook_id).
		                  first())[0]
		logger.debug(f"{self.hook_id} - got thread_ts: {self.thread_ts}")
		return self.thread_ts
