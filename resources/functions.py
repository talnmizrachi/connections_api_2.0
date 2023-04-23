import datetime
from typing import Any, Dict, List

import requests
from bs4 import BeautifulSoup
from flask import abort
from sqlalchemy.exc import SQLAlchemyError
from cross_functions.LoggingGenerator import Logger
from db import db
import pandas as pd
import os
from dotenv import load_dotenv
logger = Logger(os.path.basename(__file__).split('.')[0]).get_logger()

load_dotenv()

def parse_webhook(data_):
	logger.debug(f'{data_.get("id")} - parse_webhook')
	logger.debug(f"webook entering:\t {data_}")
	member = _get_member(data_)
	job = _get_job(data_)
	company = data_.get("employer", {}).get("name")
	logger.debug(f"job from data\t {job}")
	return {
		"hook_id": data_.get("id"),
		"action_type": data_.get("actionType"),
		"datetime": datetime.datetime.now(),
		"full_name": member.get("full_name"),
		"owner_cohort_value": member.get("cohort_value"),
		"email": member.get("email"),
		"job_title": job.get("title"),
		"job_url": job.get("url"),
		"job_id": job.get("id"),
		"job_description": job.get("description"),
		"company": company,
	}


# Webhooks
def _get_member(data: Dict[str, Any]) -> Dict[str, Any]:
	logger.debug(f'{data.get("id")} - get member')
	member = data.get("ownerMember", {})

	try:
		cohort_val = member.get("memberFieldValues", [{}])[0].get("value")
	except IndexError:
		logger.error(f"{data.get('id')} - Member not found: {member}")
		logger.debug(f"{data.get('id')} - data: {data}")
		cohort_val = None

	parsed = {
		"full_name": member.get("fullName", "").lower(),
		"cohort_value": cohort_val,
		"email": member.get("email", "").lower(),
	}

	return parsed


def _get_job(data: Dict[str, Any]) -> Dict[str, Any]:
	logger.debug(f'{data.get("id")} - get job info')
	job = data.get("job", {})
	description = job.get("htmlDescription", "")
	if len(description) > 0:
		soup = BeautifulSoup(description, "html.parser")
		desc = soup.get_text().strip().lower()
	else:
		desc = ""

	return {
		"title": job.get("title", "").lower(),
		"url": job.get("url"),
		'id': job.get("id"),
		"description": desc
	}


def committing_function(what_to_commit, hook_id=None):
	try:
		logger.debug(f"{hook_id} - what_to_commit:\t{what_to_commit}")
		db.session.add(what_to_commit)
		db.session.commit()
	except SQLAlchemyError as e:
		db.session.rollback()
		logger.error(f"{hook_id} - SQLAlchemyError - {e}")
		abort(500, str(e))


def get_event_details(calendly_link_):
	headers = {
		"Authorization": f"Bearer {os.environ['CALENDLY_TOKEN']}",
		"Content-Type": "application/json"
	}

	event_uuid = calendly_link_.split('scheduled_events/')[1].split("/invitees")[0]
	if event_uuid == 'EVENT_TYPE':
		event_uuid = '246eccc5-8cd2-473a-969a-b0f3796bd453'

	url = f"https://api.calendly.com/scheduled_events/{event_uuid}"

	response = requests.get(url, headers=headers)

	if response.status_code == 200:
		try:
			event_data = response.json()
			post_int_date = event_data['resource']['start_time'].split("T")[0]
			return post_int_date
		except Exception as e:
			print(e)
			return None


def typeform_questions_to_columns_mapper():
	mapper = {"First off, what's your email address?": "email_address",
	          "What's your full name?": "full_name",
	          "Where is the job located?": "region",
	          "What's the company name?": "company_name",
	          "What's the job title?": "job_title",
	          "What is the date of the interview?": "date_of_interview",
	          "S[et a time ](https://calendly.com/anisa_sxm_ms/30min)*[after](https://calendly.com/anisa_sxm_ms/30min)*[ the interview date for a post interview debriefing](https://calendly.com/anisa_sxm_ms/30min)": "post_interview_meeting_date",
	          "At what stage of the interview process are you?": "stage_in_funnel",
	          "Was there a home assignment you completed for ": "had_home_assignment",
	          "Please upload the home assignment": "home_assignment_questions_link",
	          "Please upload your answers to the home assignment": "home_assignment_answers_link",
	          "Please upload the resume you sent for this ": "resume_link",
	          "Please upload a .pdf file of the ": "job_description",
	          "Where did you find the job opportunity?": "source_1",
	          "Please elaborate": "source_2",
	          "Where did you find that opportunity?": "source_2",
	          "Please share the name of the group": "source_3"}

	return mapper


def parse_typeform_qa(form_response_):
	all_answers = []
	print(form_response_)
	for answer in form_response_['answers']:

		temp_dict = answer['field']

		middle = list(answer.keys())[1]
		value = answer[middle]

		if isinstance(value, dict):
			value = value['label']

		temp_dict['value'] = value
		all_answers.append(temp_dict)

	questions = pd.DataFrame(form_response_['definition']['fields'])
	questions['title'] = questions['title'].str.split("{", expand=True)[0]
	answers = pd.DataFrame(all_answers)
	base_data = questions.merge(answers)[['title', 'value']].copy()
	mapper = typeform_questions_to_columns_mapper()
	base_data['title'] = base_data['title'].map(mapper)
	base_data['value'] = base_data['value'].apply(lambda x: get_event_details(x) if str(x).find("calendly") > 0 else x)
	base_dict_ = base_data.set_index('title').to_dict()['value']

	return base_dict_


def parse_webhook_from_typeform_(data_):
	event_id = data_.get('event_id')
	form_response = data_.get('form_response', {})
	logger.debug(f'form_response - {form_response}')
	print(f'form_response - {form_response}')
	token = form_response.get('token')
	submission_time = form_response.get('submitted_at')
	base_dict = parse_typeform_qa(form_response)

	base_dict['event_id'] = event_id
	base_dict['token'] = token
	base_dict['submission_time'] = submission_time

	return base_dict

