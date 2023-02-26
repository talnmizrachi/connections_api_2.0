from flask import request
from flask_smorest import Blueprint, abort
import datetime
from resources.functions import _get_member, _get_job, _get_description
from flask.views import MethodView
from cross_functions.LoggingGenerator import Logger

def parse_webhook(data_):
    member = _get_member(data_)
    job = _get_job(data_)
    description = _get_description(data_)

    company = data_.get("employer", {}).get("name")

    return {
        "hook_id": data_.get("id"),
        "action_type": data_.get("actionType"),
        "datetime": datetime.datetime.now(),
        "owner_cohort_value": member.get("cohort_value"),
        "owner_mail": member.get("email"),
        "job_title": job.get("title"),
        "job_url": job.get("url"),
        "job_description": description,
        "company": company,
    }


logger = Logger("resources_webhooks").get_logger()

wh_blueprint = Blueprint("webhooks", __name__, description="webhooks parser")

@wh_blueprint.route("/webhooks/")
class WebHookCatcher(MethodView):

    def post(self):

        data_ = request.get_json()
        logger.debug(data_)

        if data_.get("actionType") == "TEST" and data_.get("eventType") == "TEST":
            logger.debug("actionType and eventType are TEST")
            return {"status": "ok"}

        request_data = parse_webhook(data_)
        logger.debug(request_data)


        return parse_webhook(data_)


if __name__ == '__main__':
    print(datetime.datetime.now())
