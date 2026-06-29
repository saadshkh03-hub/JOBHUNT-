from __future__ import annotations
import logging
import re
import hashlib
import httpx
from .base import BaseConnector
from ..models import SourceStatus

logger = logging.getLogger(__name__)

COUNCIL_CAREER_URLS = [
    # Major metro councils — real URLs
    {"name": "City of Sydney", "url": "https://www.cityofsydney.nsw.gov.au/council/jobs"},
    {"name": "City of Melbourne", "url": "https://www.melbourne.vic.gov.au/about-council/jobs"},
    {"name": "Brisbane City Council", "url": "https://www.brisbane.qld.gov.au/about-council/council-information-and-rates/careers"},
    {"name": "City of Perth", "url": "https://www.perth.wa.gov.au/council/employment"},
    {"name": "City of Adelaide", "url": "https://www.cityofadelaide.com.au/about-council/jobs-at-council/"},
    # Aggregators
    {"name": "Council Jobs AU", "url": "https://www.counciljobs.com.au"},
    {"name": "LG Jobs", "url": "https://lgjobs.com.au"},
]


def _quick_parse_jobs(html: str, council_name: str, source_url: str) -> list[dict]:
    """Lightweight job extraction from council career pages."""
    jobs = []
    # Look for links that contain "job" or "vacancy" or "position"
    job_link_pattern = re.compile(
        r'<a[^>]+href="([^"]*(?:job|vacanc|position|career|opportunit)[^"]*)"[^>]*>([\s\S]*?)</a>',
        re.IGNORECASE,
    )
    seen_titles = set()
    for m in job_link_pattern.finditer(html):
        link_href = m.group(1)
        link_text = re.sub(r"<[^>]+>", "", m.group(2)).strip()
        if not link_text or len(link_text) < 5 or len(link_text) > 200:
            continue
        # Filter navigation links
        skip_words = ["apply", "home", "about", "contact", "login", "register", "search"]
        if any(w in link_text.lower() for w in skip_words):
            continue
        if link_text in seen_titles:
            continue
        seen_titles.add(link_text)

        # Build absolute URL
        if link_href.startswith("http"):
            full_url = link_href
        elif link_href.startswith("/"):
            # Extract base domain
            domain_match = re.match(r"(https?://[^/]+)", source_url)
            if domain_match:
                full_url = domain_match.group(1) + link_href
            else:
                full_url = source_url + link_href
        else:
            full_url = source_url

        job_id = hashlib.md5(f"{link_text}{full_url}".encode()).hexdigest()[:12]
        jobs.append({
            "id": f"council_{job_id}",
            "title": link_text[:200],
            "employer": council_name,
            "location": "Local Government",
            "work_type": None,
            "salary": None,
            "description_snippet": f"Position at {council_name}. Visit the council website for full details.",
            "source_name": f"Council Jobs ({council_name})",
            "source_url": full_url,
            "official_url": full_url,
            "posted_date": None,
            "closing_date": None,
            "eligibility_notes": None,
        })

        if len(jobs) >= 5:
            break

    return jobs


class CouncilConnector(BaseConnector):
    name = "Council Jobs"

    async def search(
        self,
        query: str,
        location: str,
        radius_km: int = 50,
        work_type: str = "any",
        results_per_page: int = 20,
    ) -> tuple[list[dict], SourceStatus]:
        all_jobs: list[dict] = []

        # Try to fetch from council job aggregators
        aggregator_urls = [
            f"https://lgjobs.com.au/jobs?keywords={query}&location={location}",
            f"https://www.counciljobs.com.au/search?q={query}",
        ]

        fetched_any = False
        for url in aggregator_urls:
            try:
                async with httpx.AsyncClient(
                    timeout=10.0,
                    headers={"User-Agent": "Mozilla/5.0 (compatible; JobMatcher/1.0)"},
                    follow_redirects=True,
                ) as client:
                    resp = await client.get(url)
                    if resp.status_code == 200 and len(resp.text) > 1000:
                        fetched_any = True
                        jobs = _quick_parse_jobs(resp.text, "Council", url)
                        all_jobs.extend(jobs)
            except Exception as e:
                logger.debug(f"Council aggregator {url} failed: {e}")
                continue

        if all_jobs:
            return all_jobs[:results_per_page], SourceStatus(
                name=self.name,
                status="limited",
                message=f"Found {len(all_jobs)} council jobs (limited data available)",
            )

        if fetched_any:
            return [], SourceStatus(
                name=self.name,
                status="limited",
                message="Council job search uses curated sources — no matches found for this query",
            )

        return [], SourceStatus(
            name=self.name,
            status="limited",
            message="Council job search uses curated sources — direct council websites are the best source",
        )
