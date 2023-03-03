import json


def create_personlized_opening(poc_name, company, job_url_):
	opening = {
		"type": "section",
		"text": {
			"type": "mrkdwn",
			"text": f"Hey {poc_name}!\n\nWe checked and looks like you have connection(s) in *{company}*\n"
			        f"This is the <{job_url_}|link to the job>\n\n"
			        f"Would you mind connecting a student's CV to that company?"
		}
	}
	return opening


def crete_divider():
	divider = {"type": "divider"}
	return divider


def create_summary():
	connection_is_real = {
		"type": "section",
		"text": {
			"type": "mrkdwn",
			"text": ":green_heart:I can send heir resume:green_heart: will mean that we will ask the student to send us their "
			        "resume (they won't contact you directly) "
		}
	}
	pass_on_connections = {
		"type": "section",
		"text": {
			"type": "mrkdwn",
			"text": "Pass will do nothing (good for when you know the person but uncomfortable contacting them"
		}
	}
	connection_is_not_real = {
		"type": "section",
		"text": {
			"type": "mrkdwn",
			"text": ":red_circle:Connectionis NOT real:red_circle:will make sure we won't ask you about this connection "
			        "again in the near future "
		}
	}

	opening_ = connection_is_real, pass_on_connections, connection_is_not_real, crete_divider()

	return opening_


def create_connection_section(connection_name):
	connection_name_dict = {
		"type": "section",
		"text": {
			"type": "mrkdwn",
			"text": f"*{connection_name}*"
		}
	}
	return connection_name_dict


def create_connection_buttons(block_id, connection_name, hook_id, student_name, student_mail, poc_name, company_name,slack_id):
	def create_value_dict(status):
		value_dict = {
			'connection_name': connection_name,
			'conn_status': str(status),
			'hook_id': hook_id,
			'student_name': student_name,
			'student_mail': student_mail,
			"poc_name": poc_name,
			"company_name": company_name,
			"slack_id": slack_id
		}

		return json.dumps(value_dict)

	connection_buttons = {"type": "actions",
	                      "block_id": f"actionblock{block_id}",
	                      "elements": [
		                      {
			                      "type": "button",
			                      "text": {
				                      "type": "plain_text",
				                      "text": "I can send them a resume!"
			                      },
			                      "style": "primary",
			                      "value": create_value_dict(1)
		                      },
		                      {
			                      "type": "button",
			                      "text": {
				                      "type": "plain_text",
				                      "text": "Pass"
			                      },
			                      "value": create_value_dict(0)
		                      },
		                      {
			                      "type": "button",
			                      "text": {
				                      "type": "plain_text",
				                      "text": "Connection is NOT real"
			                      },
			                      "style": "danger",
			                      "value": create_value_dict(-1)
		                      }
	                      ]
	                      }
	return connection_buttons


def main(poc_name_, company_, connections_names, hook_id, student_name_, student_mail_, job_url_, slack_id):
	blocks = [create_personlized_opening(poc_name=poc_name_, company=company_, job_url_=job_url_), crete_divider()]

	for j, connection_name in enumerate(connections_names):
		if j > 0:
			blocks.append(crete_divider())
		blocks.append(create_connection_section(connection_name))
		blocks.append(create_connection_buttons(j, connection_name, hook_id=hook_id, student_name=student_name_,
		                                        student_mail=student_mail_, poc_name=poc_name_, company_name=company_,
		                                        slack_id=slack_id))

	for elem in create_summary():
		blocks.append(elem)

	return {"blocks": blocks}


if __name__ == '__main__':
	print(main("poc_name_", "Company", ["connection1", "connection2"], "hook_id", "student_name_", "student_mail_",
	           "job_url_"))
