from db import db
from uuid import uuid4


class MockInterviewRequests(db.Model):

	__tablename__ = 'mock_interviews_requests'
	__table_args__ = {'schema': 'interviews_passing'}

	event_id = db.Column(db.String, primary_key=True, unique=True)
	token = db.Column(db.String) #

	full_name = db.Column(db.String, nullable=True) #
	email_address = db.Column(db.String, nullable=True)#
	resume_link = db.Column(db.String) #
	is_v3 = db.Column(db.Boolean, nullable=True)
	region = db.Column(db.String, nullable=True)#

	date_of_interview = db.Column(db.Date, nullable=True)#
	company_name = db.Column(db.String)#
	job_title = db.Column(db.String, nullable=True)#

	job_description = db.Column(db.String)
	job_location = db.Column(db.String)

	event_stage = db.Column(db.String)#
	had_home_assignment = db.Column(db.Boolean)#
	home_assignment_questions_link = db.Column(db.String)#
	home_assignment_answers_link = db.Column(db.String)#

	source_1 = db.Column(db.String)#
	source_2 = db.Column(db.String)#
	source_3 = db.Column(db.String)  #

	is_pass = db.Column(db.String, nullable=True)

	mentor = db.Column(db.String)
	date_of_mock_interview = db.Column(db.Date, nullable=True)

	recording_link = db.Column(db.String)
	stage_in_funnel = db.Column(db.String)
	post_interview_meeting_date = db.Column(db.DateTime)
	submission_time = db.Column(db.DateTime)









