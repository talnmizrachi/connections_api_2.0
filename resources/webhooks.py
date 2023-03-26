from flask import request
from flask_smorest import Blueprint, abort
import datetime
from sqlalchemy import func
from models import WebhooksModel, ConnectionModel, CommunicationsModel, StudentSlackIDsModel
from resources.functions import parse_webhook, committing_function
from flask.views import MethodView
from cross_functions.LoggingGenerator import Logger
import os

from slack_bot import MatchMaker

"""

Add a checkup if the student is authorized to access the app   

"""

logger = Logger(os.path.basename(__file__).split('.')[0]).get_logger()
blueprint = Blueprint("webhooks", __name__, description="webhooks parser")
logger.debug("Webhook blueprint loaded")


def no_connections_process(matchmaker_: MatchMaker):
	matchmaker_.define_and_send_slack_msg_for_student("NO_CONNECTIONS")

	logger.debug(f"{matchmaker_.hook_id} - Company {matchmaker_.company} not found in connections db")
	abort(400, message=f"Company {matchmaker_.company} not found in connections db")


@blueprint.route("/webhooks/")
class WebHookCatcher(MethodView):

	@staticmethod
	def _get_connection_in_company(company_, hook_id):
		logger.debug(f"{hook_id} - Getting connection from company")
		# check if company is in connections db
		connections = (ConnectionModel
		               .query
		               .with_entities(ConnectionModel.contact_name, ConnectionModel.poc_name)
		               .filter(func.lower(ConnectionModel.company_name) == company_.lower())
		               .filter(ConnectionModel.is_true_connection.isnot(False))
		               .all()
		               )
		return connections

	@staticmethod
	def _is_email_authorized(request_data_, hook_id):

		email_ = request_data_.get("email")
		logger.debug(f"{hook_id} Checking if email {email_} is authorized")
		# check if company is in connections db
		slack_ids = (StudentSlackIDsModel
		             .query
		             .with_entities(StudentSlackIDsModel.student_email,
		                            StudentSlackIDsModel.slack_id,
		                            StudentSlackIDsModel.student_name)
		             .filter(func.lower(StudentSlackIDsModel.student_email) == email_.lower())
		             .first()
		             )

		if slack_ids is None:
			logger.debug(f"{hook_id} - Student {request_data_['full_name'].capitalize()} ({email_}) is not authorized")
			abort(400, message=f"Student {request_data_['full_name'].capitalize()} ({email_}) is not authorized")

	def commit_communication_from_huntr(self, request_data, hook_id):
		logger.debug(f"{hook_id} - commit_communication_from_huntr: {request_data}")
		first_communication = dict(thread_ts=None,
		                           hook_id=request_data.get("hook_id"),
		                           job_id=request_data.get("id"),
		                           event="MSG_FROM_HUNTR",
		                           message_type="INITIATION",
		                           company=request_data.get("company"),
		                           full_name=request_data.get("full_name"),
		                           student_email=request_data.get("email"),
		                           )

		committing_function(CommunicationsModel(**first_communication), hook_id)

	@staticmethod
	def commit_webhook_from_huntr(request_data):
		logger.debug(f"{request_data.get('hook_id')} - committing webhook from huntr")

		this_request_data = request_data.copy()
		del this_request_data["job_id"]
		webhook = WebhooksModel(**this_request_data)
		committing_function(what_to_commit=webhook, hook_id=this_request_data.get("hook_id"))

	def post(self):
		logger.debug(f"Process start")
		data_ = request.get_json()

		if data_.get("actionType") == "TEST" and data_.get("eventType") == "TEST":
			logger.debug("actionType and eventType are TEST")
			return {"status": "ok"}

		request_data = parse_webhook(data_)
		company = request_data.get("company")
		hook_id = request_data.get("hook_id")
		email_ = request_data.get("email")
		job_url = request_data.get("job_url")
		job_id = request_data.get("job_id", {})

		logger.debug(f"{hook_id} - checking if company is None")
		if company is None or hook_id is None:
			logger.critical(f"company is {company}\nHook_id is {hook_id}")
			abort(400, "company/Hook ID required is required")

		self.commit_webhook_from_huntr(request_data)
		self._is_email_authorized(request_data, hook_id)
		self.commit_communication_from_huntr(request_data, hook_id)

		connections = self._get_connection_in_company(company, hook_id)

		logger.debug(f"{hook_id} - initiating Matchmaker")
		matchmaker = MatchMaker(hook_id=hook_id, company=company, student_mail=email_, job_id=job_id)
		matchmaker.student_name_setter(student_name=request_data.get("full_name"))
		matchmaker.connections_setter(connections=connections)

		if len(connections) == 0:
			no_connections_process(matchmaker)

		matchmaker.define_and_send_slack_msg_for_student('CHECKING_CONNECTIONS_WITH_POCS')
		matchmaker.define_and_send_slack_msg_for_poc(job_url=job_url, email=email_,
		                                             message_type="CHECKING_STATE_OF_CONNECTIONS")

		return request_data


if __name__ == '__main__':
	print(datetime.datetime.now())
	x = 1
	y = {"thread_ts": x,
	     "event": x,
	     "message_type": x,
	     "company": x,
	     "cv_link": x,
	     "file_name": x,
	     "student_name": x,
	     "student_slack_id": x,
	     "poc_name": x,
	     "poc_slack_id": x,
	     "poc_approved_name_of_connection": x,
	     "slack_file_token": x}
