from flask import request
from flask_smorest import Blueprint, abort
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from db import db
from models import HuntrJobMovmentModel
from flask.views import MethodView
from cross_functions.LoggingGenerator import Logger
import os

from schemas import ConnectionSchema

logger = Logger(os.path.basename(__file__).split('.')[0]).get_logger()
job_movement_blueprint = Blueprint("job_movement", __name__, description="job movement receivers")
logger.debug("Connections blueprint loaded")


@job_movement_blueprint.route("/job_move/")
class JobMove(MethodView):
	# add a new connection
	def post(self):
		data = request.get_json()

		if data.get("actionType") == "TEST" and data.get("eventType") == "TEST":
			logger.debug("actionType and eventType are TEST")
			return {"status": "ok"}

		job = data.get("job", {})
		student = data.get("ownerMember")

		job_mvmnt_obj = {
			"job_id": job.get("id"),
			"job_title": job.get("title"),
			"datetime": data.get('date'),
			"action": data.get('actionType'),
			"student_mail": student.get("email"),
			"student_full_name": student.get("fullName"),
			"company": data.get("employer", {}).get("name"),
			"from_list": data.get("fromList")['name'],
			"to_list": data.get("toList")['name'],
		}

		job_mvmnt_obj = HuntrJobMovmentModel(**job_mvmnt_obj)

		try:
			db.session.add(job_mvmnt_obj)
			db.session.commit()
		except SQLAlchemyError as e:
			db.session.rollback()
			logger.error(e)
