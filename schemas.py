from marshmallow import Schema, fields
from uuid import uuid4


class WebhookSchema(Schema):
	id = fields.Str(data_key='id', required=True)
	action_type = fields.Str(data_key='actionType', required=True)
	owner_member = fields.Dict(data_key='ownerMember', required=True)
	job = fields.Dict(data_key='job', required=True)


class StudentSlackIdSchema(Schema):
	student_name = fields.Str(required=True)
	slack_id = fields.Str(required=True)
	student_mail = fields.Str(required=True)


class POCSlackIdSchema(Schema):
	poc_name = fields.Str(required=True)
	slack_id = fields.Str(required=True)
	poc_slack_name = fields.Str(required=True)


class ConnectionSchema(Schema):
	id = fields.Str(dump_only=True)
	contact_name = fields.Str(required=True)
	poc_name = fields.Str(required=True)
	company_name = fields.Str(required=True)
	is_true_connection = fields.Boolean(required=False)


class SlackEventSchema(Schema):
	token = fields.Str()
	challenge = fields.Str()
	type = fields.Str()
