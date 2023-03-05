from flask import request
from flask_smorest import Blueprint, abort
from slack_sdk import WebClient
from sqlalchemy import or_
from sqlalchemy.exc import SQLAlchemyError
from db import db
from flask.views import MethodView
from cross_functions.LoggingGenerator import Logger
import os
from models import StudentSlackIDsModel

logger = Logger(os.path.basename(__file__).split('.')[0]).get_logger()
blueprint = Blueprint("student_slack_ids", __name__, description="actions related to student slack ids")


def send_welcoming_message(slack_id):
    bulbs = ":bulb::bulb::bulb:"
    opening = f"{bulbs}Sending resumes via connections can be important as it can increase the chances of your resume being " \
              "noticed and lead to more opportunities as compared to submitting your application through " \
              f"a traditional online application process - and that's why I'm here{bulbs}."

    body = "Everytime you save a position to your *wishlist* on Huntr, I will check with all of our Masterschool " \
           "network of connections and see if we can send your resumes via one of them." \
           "If I'll find a connection that is willing to forward your resumes, I will contact you on the same thread " \
           "that you got from me about that position." \
           "While I'm looking for a connection that willing to forward your resumes, it's up to you to tailor your " \
           "resume to fit the job description - if you have any questions, feel free to contact me on #astrid-questions-and-bugs channel." \

    WebClient(token=os.environ.get("SLACK_OAUTH_TOKEN")).chat_postMessage(channel=slack_id, text=f"{opening}\n\n{body}")



@blueprint.route("/student_slack_id/")
class StudentSlackId(MethodView):

    #Add new students (slack_id, student_name, email and id)
    # get new student slack id
    def post(self):
        req_data = request.get_json()
        student_name = req_data.get('student_name')
        slack_id = req_data.get('slack_id')
        student_email = req_data.get('student_email')

        if student_name is None or slack_id is None or student_email is None:
            abort(400, message="Missing required fields")

        student_slack_id = StudentSlackIDsModel(**req_data)

        try:
            logger.info(f"Adding new student {student_slack_id}")
            db.session.add(student_slack_id)
            db.session.commit()
            send_welcoming_message(slack_id)
            return {"status": "success", "message": "Student added successfully"}, 201
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"SQLAlchemyError - {e}")
            abort(500, str(e))


@blueprint.route("/student_slack_ids/")
class StudentSlackIds(MethodView):
    def post(self):
        """add a group of students, if you want to add only one student, you can also use this endpoint
        because I'm lazy

        """
        data = request.get_json()

        conns = (StudentSlackIDsModel(**x) for x in data)

        try:
            db.session.add_all(conns)
            db.session.commit()
            response = {
                "status": "success",
                "message": "Student added successfully"
            }
            return response, 201

        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"SQLAlchemyError - {e}")
            abort(500, str(e))

    def get(self):
        data = request.get_json()
        slack_id = data.get('slack_id')
        student_email = data.get('student_email')

        if slack_id is None and student_email is None:
            abort(400, message="Missing required fields")

        students = (StudentSlackIDsModel.
                    query.
                    with_entities(StudentSlackIDsModel.slack_id, StudentSlackIDsModel.student_name).
                    filter(or_(StudentSlackIDsModel.slack_id == slack_id,
                               StudentSlackIDsModel.student_email == student_email)).
                    all()
                    )
        logger.info(students)
        if len(students) == 0:
            abort(404, message="Student not found")

        response = {
            "status": "success",
            "student": {'slack_id': students[0][0], 'student_name': students[0][1]}
        }
        return response, 200
