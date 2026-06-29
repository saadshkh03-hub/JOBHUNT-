from __future__ import annotations
import logging
import re
import hashlib
from typing import Optional
import httpx
from .base import BaseConnector
from ..models import SourceStatus

logger = logging.getLogger(__name__)

APS_RSS_URL = "https://www.apsjobs.gov.au/s/search-rss"
APS_SEARCH_URL = "https://www.apsjobs.gov.au/s/search"
APS_BASE = "https://www.apsjobs.gov.au"


def _extract_employer_from_text(text: str) -> str:
    """Try to extract the agency name from description text."""
    patterns = [
        r"(?:with|at|for)\s+(?:the\s+)?([A-Z][A-Za-z\s&]+(?:Department|Agency|Office|Commission|Authority|Board|Service|Institute|Council))",
        r"^([A-Z][A-Za-z\s&]+(?:Department|Agency|Office|Commission|Authority|Board|Service|Institute|Council))",
    ]
    for pattern in patterns:
        m = re.search(pattern, text, re.MULTILINE)
        if m:
            name = m.group(1).strip()
            if len(name) < 100:
                return name
    return "Australian Public Service"


def _parse_rss_entries(feed_text: str) -> list[dict]:
    """Parse RSS XML to extract job listings."""
    jobs = []
    # Parse <item> blocks
    item_pattern = re.compile(r"<item>([\s\S]*?)</item>", re.IGNORECASE)
    for item_match in item_pattern.finditer(feed_text):
        item = item_match.group(1)

        def get_tag(tag: str) -> str:
            m = re.search(rf"<{tag}[^>]*>([\s\S]*?)</{tag}>", item, re.IGNORECASE)
            if m:
                content = m.group(1)
                # Strip CDATA
                content = re.sub(r"<!\[CDATA\[([\s\S]*?)\]\]>", r"\1", content)
                # Strip HTML tags
                content = re.sub(r"<[^>]+>", " ", content)
                return content.strip()
            return ""

        title = get_tag("title")
        link = get_tag("link")
        description = get_tag("description")
        pub_date = get_tag("pubDate")
        category = get_tag("category")

        if not title or not link:
            continue

        # Extract employer from description or category
        employer = _extract_employer_from_text(description) if description else "Australian Public Service"
        if category and len(category) < 80:
            employer = category

        # Determine location from description
        location = _extract_location_from_text(description + " " + title)

        job_id = hashlib.md5(link.encode()).hexdigest()[:12]

        jobs.append({
            "id": f"aps_{job_id}",
            "title": title[:200],
            "employer": employer[:100],
            "location": location or "Canberra, ACT",
            "work_type": None,
            "salary": _extract_salary(description),
            "description_snippet": description[:600] if description else "",
            "source_name": "APS Jobs",
            "source_url": link,
            "official_url": link,
            "posted_date": pub_date[:20] if pub_date else None,
            "closing_date": _extract_closing_date(description),
            "eligibility_notes": "Australian citizenship may be required for APS roles",
        })

    return jobs


def _extract_location_from_text(text: str) -> str:
    aus_cities = [
        "Canberra", "Sydney", "Melbourne", "Brisbane", "Perth", "Adelaide",
        "Hobart", "Darwin", "ACT", "NSW", "VIC", "QLD", "WA", "SA", "TAS", "NT",
    ]
    text_lower = text.lower()
    for city in aus_cities:
        if city.lower() in text_lower:
            return city
    return "Canberra, ACT"  # Most APS jobs are in Canberra


def _extract_salary(text: str) -> Optional[str]:
    patterns = [
        r"\$[\d,]+\s*[-–]\s*\$[\d,]+",
        r"APS\s*\d+\s*\([\$\d,\s\-–]+\)",
        r"salary\s+(?:of\s+)?\$[\d,]+",
        r"\$[\d,]+\s+(?:per\s+annum|p\.?a\.?|annually)",
    ]
    for pattern in patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            return m.group(0).strip()[:80]
    return None


def _extract_closing_date(text: str) -> Optional[str]:
    patterns = [
        r"(?:closes?|closing|applications\s+close)[:\s]+(\d{1,2}[\s/\-]\w+[\s/\-]\d{2,4})",
        r"(?:closes?|closing)[:\s]+(\w+\s+\d{1,2},?\s+\d{4})",
        r"applications\s+(?:close|due)[:\s]+([^\n]{5,30})",
    ]
    for pattern in patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            return m.group(1).strip()[:30]
    return None


def _parse_html_jobs(html_text: str) -> list[dict]:
    """Very basic HTML parsing for APS jobs page — fallback if RSS fails."""
    jobs = []
    # Look for job listing patterns in HTML
    title_pattern = re.compile(
        r'<h[23][^>]*class="[^"]*(?:title|heading|job)[^"]*"[^>]*>([\s\S]*?)</h[23]>',
        re.IGNORECASE,
    )
    link_pattern = re.compile(r'href="(/s/job-detail[^"]+)"', re.IGNORECASE)

    titles = title_pattern.findall(html_text)
    links = link_pattern.findall(html_text)

    for i, (title_html, link_path) in enumerate(zip(titles, links)):
        title = re.sub(r"<[^>]+>", "", title_html).strip()
        if not title:
            continue
        url = f"{APS_BASE}{link_path}"
        job_id = hashlib.md5(url.encode()).hexdigest()[:12]
        jobs.append({
            "id": f"aps_{job_id}",
            "title": title[:200],
            "employer": "Australian Public Service",
            "location": "Canberra, ACT",
            "work_type": None,
            "salary": None,
            "description_snippet": "",
            "source_name": "APS Jobs",
            "source_url": url,
            "official_url": url,
            "posted_date": None,
            "closing_date": None,
            "eligibility_notes": "Australian citizenship may be required for APS roles",
        })

    return jobs[:20]


class APSConnector(BaseConnector):
    name = "APS Jobs"

    async def search(
        self,
        query: str,
        location: str,
        radius_km: int = 50,
        work_type: str = "any",
        results_per_page: int = 20,
    ) -> tuple[list[dict], SourceStatus]:
        jobs: list[dict] = []

        # Try RSS first
        try:
            rss_params = {"q": query}
            if location:
                rss_params["positionLocation"] = location

            async with httpx.AsyncClient(
                timeout=15.0,
                headers={"User-Agent": "Mozilla/5.0 (compatible; JobMatcher/1.0)"},
                follow_redirects=True,
            ) as client:
                rss_response = await client.get(APS_RSS_URL, params=rss_params)
                if rss_response.status_code == 200:
                    rss_text = rss_response.text
                    if "<item>" in rss_text or "<channel>" in rss_text:
                        jobs = _parse_rss_entries(rss_text)
                        if jobs:
                            return jobs, SourceStatus(
                                name=self.name,
                                status="available",
                                message=f"Found {len(jobs)} APS jobs via RSS",
                            )

                # Fallback: try HTML search
                html_params = {"q": query}
                if location:
                    html_params["positionLocation"] = location
                html_response = await client.get(APS_SEARCH_URL, params=html_params)
                if html_response.status_code == 200:
                    jobs = _parse_html_jobs(html_response.text)
                    if jobs:
                        return jobs, SourceStatus(
                            name=self.name,
                            status="limited",
                            message=f"Found {len(jobs)} APS jobs (limited data from HTML)",
                        )

            return [], SourceStatus(
                name=self.name,
                status="limited",
                message="APS Jobs returned no results for this search",
            )

        except httpx.TimeoutException:
            logger.warning("APS Jobs request timed out")
            return [], SourceStatus(
                name=self.name,
                status="unavailable",
                message="APS Jobs site timed out — try again later",
            )
        except httpx.HTTPStatusError as e:
            logger.warning(f"APS Jobs HTTP error: {e.response.status_code}")
            return [], SourceStatus(
                name=self.name,
                status="unavailable",
                message=f"APS Jobs returned HTTP {e.response.status_code}",
            )
        except Exception as e:
            logger.error(f"APS connector error: {e}")
            return [], SourceStatus(
                name=self.name,
                status="unavailable",
                message=f"APS Jobs unavailable: {str(e)[:100]}",
            )
