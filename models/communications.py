from datetime import datetime

from db import db
from uuid import uuid4


class CommunicationsModel(db.Model):

	__tablename__ = 'communications'

	id = db.Column(db.String, primary_key=True, default=lambda: str(uuid4().hex), unique=True)
	hook_id = db.Column(db.String, db.ForeignKey('webhooks.hook_id'), unique=False, nullable=False)
	webhooks = db.relationship('WebhooksModel', back_populates='communications')

	thread_ts = db.Column(db.String)
	event = db.Column(db.String, nullable=False)
	message_type = db.Column(db.String, nullable=False)
	company = db.Column(db.String)
	cv_link = db.Column(db.String, nullable=True)
	file_name = db.Column(db.String, nullable=True)
	full_name = db.Column(db.String, nullable=True)
	student_slack_id = db.Column(db.String, nullable=True)
	student_email = db.Column(db.String, nullable=True)
	poc_name = db.Column(db.String, nullable=True)
	poc_slack_id = db.Column(db.String, nullable=True)
	slack_file_token = db.Column(db.String, nullable=True)
	approved_connection_name = db.Column(db.String, nullable=True)
	communication_timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
