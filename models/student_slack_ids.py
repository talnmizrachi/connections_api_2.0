from uuid import uuid4

from db import db


class StudentSlackIDsModel(db.Model):

	__tablename__ = 'student_slack_ids'

	id = db.Column(db.String, primary_key=True, default=lambda: str(uuid4().hex), unique=True)
	student_name = db.Column(db.String, nullable=False)
	slack_id = db.Column(db.String, nullable=False)
	student_email = db.Column(db.String, nullable=False)

	__table_args__ = (
		db.UniqueConstraint('slack_id', 'student_email', name='unique_slack_id_email_for_student'),
	)