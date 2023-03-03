from db import db
from uuid import uuid4


class ConnectionModel(db.Model):

	__tablename__ = 'connections'

	__table_args__ = (
		db.UniqueConstraint('contact_name', 'poc_name', 'company_name', name='_contact_name_poc_name_company_name_uc'),
	)

	id = db.Column(db.String, primary_key=True, default=lambda: str(uuid4().hex), unique=True)
	contact_name = db.Column(db.String(255), unique=False, nullable=False)
	poc_name = db.Column(db.String(255), unique=False, nullable=False)
	company_name = db.Column(db.String(255), unique=False, nullable=False)
	is_true_connection = db.Column(db.Boolean, unique=False, nullable=True)
	response_date = db.Column(db.DateTime, default=None, nullable=True)

	def __str__(self):
		return f'<Connection between {self.poc_name} and {self.contact_name} (from {self.company_name})>'

	def __repr__(self):
		return f'ConnectionsModel(contact_name={self.contact_name},' \
		       f' poc_name={self.poc_name},' \
		       f' company_={self.company_name},' \
		       f' is_true_connection={self.is_true_connection}, response_date={self.response_date})'
