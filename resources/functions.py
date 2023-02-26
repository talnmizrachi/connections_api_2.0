from typing import Any, Dict, List
from bs4 import BeautifulSoup


##Webhooks
def _get_member(data: Dict[str, Any]) -> Dict[str, Any]:
    member = data.get("ownerMember", {})
    return {
        "full_name": member.get("fullName", "").lower(),
        "cohort_value": member.get("memberFieldValues", [{}])[0].get("value"),
        "email": member.get("email", "").lower(),
    }

def _get_job(data: Dict[str, Any]) -> Dict[str, Any]:
    job = data.get("job", {})
    return {
        "title": job.get("title", "").lower(),
        "url": job.get("url"),
    }

def _get_description(data: Dict[str, Any]) -> str:
    description = data.get("job", {}).get("htmlDescription", "")
    if len(description) > 0:
        soup = BeautifulSoup(description, "html.parser")
        return soup.get_text().strip()
    else:
        return ""