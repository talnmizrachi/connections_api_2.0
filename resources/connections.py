from flask import request, jsonify
from flask_smorest import Blueprint, abort
from sqlalchemy import func, or_
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from db import db
from models.connections import ConnectionModel
from flask.views import MethodView
from cross_functions.LoggingGenerator import Logger
import os

from schemas import ConnectionSchema

logger = Logger(os.path.basename(__file__).split('.')[0]).get_logger()
connections_blueprint = Blueprint("connections", __name__, description="actions related to POCs' connections")
connection_blueprint = Blueprint("connection", __name__, description="actions related to POCs' connections")
logger.debug("Connections blueprint loaded")


@connection_blueprint.route("/connection/")
class Connection(MethodView):
	# add a new connection
	def post(self):
		logger.info("POST /connection/")
		data = request.get_json()
		contact_name = data.get('contact_name')
		poc_name = data.get('poc_name')
		company_name = data.get('company_name')

		connection = ConnectionModel(**data)

		try:
			db.session.add(connection)
			db.session.commit()
			response = {
				"status": "success",
				"message": "connection added successfully"
			}
			return response, 201
		except IntegrityError as ie:
			msg = f"Connection between {poc_name} and {contact_name} in {company_name} already exists - {ie}"
			logger.warning(msg)
			db.session.rollback()
			response = {
				"status": "error",
				"message": msg
			}
			return abort(409, message=response)

		except SQLAlchemyError as e:
			logger.error(e)
			db.session.rollback()
			response = {
				"status": "error",
				"message": "connection could not be added"
			}
			return abort(500, message=response)

	def get(self):
		logger.info("GET /connection/")
		try:
			connections = ConnectionModel.query.all()
			return ConnectionSchema(many=True).dump(connections), 200

		except SQLAlchemyError as e:
			logger.error(e)
			db.session.rollback()
			response = {
				"status": "error",
				"message": "connection could not be retrieved"
			}
			return abort(500, message=response)


@connections_blueprint.route("/connections")
class Connections(MethodView):

	def post(self):
		logger.info("POST /connections/")
		data = request.get_json()

		conns = (ConnectionModel(**x) for x in data)

		try:
			db.session.add_all(conns)
			db.session.commit()
			response = {
				"status": "success",
				"message": "connections added successfully"
			}
			return response, 201
		except SQLAlchemyError as e:
			logger.error(e)
			db.session.rollback()
			response = {
				"status": "error",
				"message": "connections could not be added"
			}
		return abort(405, response)


@connection_blueprint.route('/true_connections', methods=['GET'])
def get_connections():
	attribute1_val = request.args.get('company_name').lower()

	results = ConnectionModel.query.filter(
		func.lower(ConnectionModel.company_name) == attribute1_val,
		or_(ConnectionModel.is_true_connection == True, ConnectionModel.is_true_connection.is_(None))
	)

	# Create a list of dictionaries (as you can't jsonify a SQLAlchemy object directly)
	list_results = []
	for result in results:
		list_results.append({"POC": result.poc_name, "contact": result.contact_name, "is_true_connection": result.is_true_connection})

	return jsonify(list_results)
