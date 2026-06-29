from __future__ import annotations
import logging
from typing import Optional
import httpx
from .base import BaseConnector
from ..models import SourceStatus

logger = logging.getLogger(__name__)

ADZUNA_BASE_URL = "https://api.adzuna.com/v1/api/jobs/au/search/1"

WORK_TYPE_MAP = {
    "permanent": "onsite",
    "contract": "onsite",
    "part_time": "onsite",
    "full_time": "onsite",
}


def _map_work_type(contract_type: Optional[str]) -> Optional[str]:
    if not contract_type:
        return None
    return WORK_TYPE_MAP.get(contract_type.lower(), contract_type)


def _parse_salary(job_dict: dict) -> Optional[str]:
    salary_min = job_dict.get("salary_min")
    salary_max = job_dict.get("salary_max")
    if salary_min and salary_max:
        try:
            lo = int(float(salary_min))
            hi = int(float(salary_max))
            if lo > 0 and hi > 0:
                return f"${lo:,} – ${hi:,} AUD"
            elif lo > 0:
                return f"From ${lo:,} AUD"
        except (ValueError, TypeError):
            pass
    return None


def _extract_location(job_dict: dict) -> str:
    loc = job_dict.get("location", {})
    if isinstance(loc, dict):
        display_name = loc.get("display_name", "")
        area = loc.get("area", [])
        if display_name:
            return display_name
        if area:
            return ", ".join(str(a) for a in area[-2:])
    if isinstance(loc, str):
        return loc
    return "Australia"


def _raw_job_from_adzuna(item: dict, source_name: str = "Adzuna") -> dict:
    title = item.get("title", "")
    employer_info = item.get("company", {})
    if isinstance(employer_info, dict):
        employer = employer_info.get("display_name", "Unknown Employer")
    else:
        employer = str(employer_info) if employer_info else "Unknown Employer"

    description = item.get("description", "")
    redirect_url = item.get("redirect_url", "")
    contract_type = item.get("contract_type") or item.get("contract_time")

    return {
        "id": str(item.get("id", "")),
        "title": title,
        "employer": employer,
        "location": _extract_location(item),
        "work_type": _map_work_type(contract_type),
        "salary": _parse_salary(item),
        "description_snippet": description[:600] if description else "",
        "source_name": source_name,
        "source_url": redirect_url,
        "official_url": redirect_url,
        "posted_date": item.get("created", ""),
        "closing_date": None,
        "eligibility_notes": None,
    }


class AdzunaConnector(BaseConnector):
    name = "Adzuna"

    def __init__(self, app_id: Optional[str] = None, app_key: Optional[str] = None):
        self.app_id = app_id
        self.app_key = app_key

    def _has_credentials(self) -> bool:
        return bool(self.app_id and self.app_key)

    def get_status(self) -> SourceStatus:
        if not self._has_credentials():
            return SourceStatus(
                name=self.name,
                status="unavailable",
                message="Configure ADZUNA_APP_ID and ADZUNA_APP_KEY in .env to enable Adzuna job search",
            )
        return SourceStatus(name=self.name, status="available")

    async def search(
        self,
        query: str,
        location: str,
        radius_km: int = 50,
        work_type: str = "any",
        results_per_page: int = 20,
    ) -> tuple[list[dict], SourceStatus]:
        if not self._has_credentials():
            return [], SourceStatus(
                name=self.name,
                status="unavailable",
                message="Configure ADZUNA_APP_ID and ADZUNA_APP_KEY to enable Adzuna. Get free keys at https://developer.adzuna.com/",
            )

        params: dict = {
            "app_id": self.app_id,
            "app_key": self.app_key,
            "what": query,
            "results_per_page": results_per_page,
            "content-type": "application/json",
        }
        if location:
            params["where"] = location
        if radius_km:
            params["distance"] = radius_km

        # Map work_type filter to Adzuna's full_time/part_time params
        if work_type == "remote":
            params["what"] += " remote"

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(ADZUNA_BASE_URL, params=params)
                response.raise_for_status()
                data = response.json()

            results = data.get("results", [])
            if not isinstance(results, list):
                results = []

            jobs = [_raw_job_from_adzuna(item) for item in results]
            status = SourceStatus(
                name=self.name,
                status="available",
                message=f"Found {len(jobs)} jobs",
            )
            return jobs, status

        except httpx.HTTPStatusError as e:
            logger.warning(f"Adzuna HTTP error: {e.response.status_code}")
            return [], SourceStatus(
                name=self.name,
                status="unavailable",
                message=f"Adzuna API returned HTTP {e.response.status_code}",
            )
        except httpx.TimeoutException:
            logger.warning("Adzuna request timed out")
            return [], SourceStatus(
                name=self.name,
                status="unavailable",
                message="Adzuna API timed out",
            )
        except Exception as e:
            logger.error(f"Adzuna connector error: {e}")
            return [], SourceStatus(
                name=self.name,
                status="unavailable",
                message=f"Adzuna unavailable: {str(e)[:100]}",
            )
