from db import db
from uuid import uuid4


class WebhooksModel(db.Model):

	__tablename__ = 'webhooks'

	hook_id = db.Column(db.String, primary_key=True, default=lambda: str(uuid4().hex), unique=True)

	action_type = db.Column(db.String)
	datetime = db.Column(db.DateTime)
	full_name = db.Column(db.String, nullable=True)
	owner_cohort_value = db.Column(db.String)
	email = db.Column(db.String, nullable=False)
	job_title = db.Column(db.String)
	job_url = db.Column(db.String)
	job_description = db.Column(db.String)
	job_id = db.Column(db.String)
	company = db.Column(db.String, nullable=False)

	communications = db.relationship('CommunicationsModel', back_populates='webhooks', lazy='dynamic')








