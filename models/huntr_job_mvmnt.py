from db import db
from uuid import uuid4


class HuntrJobMovmentModel(db.Model):

	__tablename__ = 'huntr_job_mvmnt'

	huntr_job_mvmnt_id = db.Column(db.String, primary_key=True, default=lambda: str(uuid4().hex), unique=True)

	job_id = db.Column(db.String)
	datetime = db.Column(db.DateTime, nullable=False)

	action_type = db.Column(db.String)
	student_mail = db.Column(db.String, nullable=False)
	full_name = db.Column(db.String, nullable=True)

	job_title = db.Column(db.String)
	company = db.Column(db.String, nullable=False)

	from_list = db.Column(db.String, nullable=False)
	to_list = db.Column(db.String, nullable=False)


	__table_args__ = (
		db.UniqueConstraint('job_id','datetime', 'action_type', 'from_list', 'to_list', name='_job_id_action_type_from_list_to_list_uc'),
	)








