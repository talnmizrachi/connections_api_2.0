from uuid import uuid4

from db import db


class POCSlackIDsModel(db.Model):

	__tablename__ = 'poc_slack_ids'
	id = db.Column(db.String, primary_key=True, default=lambda: str(uuid4().hex), unique=True)
	poc_name = db.Column(db.String)
	slack_id = db.Column(db.String)

	__table_args__ = (
		db.UniqueConstraint('poc_name', 'slack_id', name='unique_slack_id_email'),
	)
