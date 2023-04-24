import datetime
import json

import requests
from flask import request
from flask_smorest import Blueprint, abort, response
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from db import db
from models import MockInterviewRequests
from flask.views import MethodView
from cross_functions.LoggingGenerator import Logger
import os
from resources.functions import parse_webhook_from_typeform_
from schemas import ConnectionSchema

logger = Logger(os.path.basename(__file__).split('.')[0]).get_logger()
mock_int_blueprint = Blueprint("mock_interview_request", __name__, description="mock interview request from typeform")
logger.debug("Connections blueprint loaded")


@mock_int_blueprint.route("/set_mock_interview/")
class MockSetter(MethodView):
	# add a new mock request from typeform
	def post(self):
		data = request.get_json()

		mock_int_dict = parse_webhook_from_typeform_(data)
		mock_int_obj = MockInterviewRequests(**mock_int_dict)
		logger.debug(mock_int_dict)
		
		try:
			db.session.add(mock_int_obj)
			db.session.commit()
		except SQLAlchemyError as e:
			db.session.rollback()
			logger.error(e)

		return mock_int_dict


@mock_int_blueprint.route("/copy_mock_interview_from_past_data/")
class MockCopier(MethodView):
	def post(self):
		data = request.get_json()
		mock_int_obj = MockInterviewRequests(**data)

		try:
			db.session.add(mock_int_obj)
			db.session.commit()

		except SQLAlchemyError as e:
			db.session.rollback()
			logger.error(e)

		return data