from __future__ import annotations
import hashlib
import logging
import re
from typing import Optional

import httpx

from .base import BaseConnector
from ..models import SourceStatus

logger = logging.getLogger(__name__)

JORA_SEARCH_URL = "https://au.jora.com/j"


def _parse_salary(text: str) -> Optional[str]:
    patterns = [
        r"\$[\d,]+\s*[-–]\s*\$[\d,]+(?:\s*(?:per\s+annum|pa|p\.a\.|annually|\/yr|\/year))?",
        r"\$[\d,]+(?:\s*(?:per\s+annum|pa|p\.a\.|annually|\/yr|\/year))",
    ]
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            return m.group(0).strip()[:80]
    return None


def _clean_text(html: str) -> str:
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"&amp;", "&", text)
    text = re.sub(r"&lt;", "<", text)
    text = re.sub(r"&gt;", ">", text)
    text = re.sub(r"&nbsp;", " ", text)
    text = re.sub(r"&#\d+;", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _infer_work_type(text: str) -> Optional[str]:
    t = text.lower()
    if "remote" in t:
        return "remote"
    if "hybrid" in t:
        return "hybrid"
    if "onsite" in t or "on-site" in t or "on site" in t:
        return "onsite"
    return None


def _parse_jora_html(html: str, source_base: str) -> list[dict]:
    jobs: list[dict] = []

    job_blocks = re.split(r'(?=<article|<div[^>]+class="[^"]*job-card[^"]*")', html)

    for block in job_blocks[:40]:
        if len(block) < 100:
            continue

        title_m = re.search(
            r'<h2[^>]*>[\s\S]*?<a[^>]+href="([^"]+)"[^>]*>([\s\S]*?)</a>[\s\S]*?</h2>',
            block, re.IGNORECASE,
        )
        if not title_m:
            title_m = re.search(
                r'<a[^>]+class="[^"]*job-title[^"]*"[^>]+href="([^"]+)"[^>]*>([\s\S]*?)</a>',
                block, re.IGNORECASE,
            )
        if not title_m:
            continue

        href = title_m.group(1).strip()
        title_html = title_m.group(2).strip()
        title = _clean_text(title_html)
        if not title or len(title) < 3:
            continue

        if href.startswith("/"):
            url = "https://au.jora.com" + href
        elif href.startswith("http"):
            url = href
        else:
            continue

        employer_m = re.search(
            r'<span[^>]+class="[^"]*company[^"]*"[^>]*>([\s\S]*?)</span>',
            block, re.IGNORECASE,
        )
        employer = _clean_text(employer_m.group(1)) if employer_m else "Unknown Employer"

        location_m = re.search(
            r'<span[^>]+class="[^"]*location[^"]*"[^>]*>([\s\S]*?)</span>',
            block, re.IGNORECASE,
        )
        location = _clean_text(location_m.group(1)) if location_m else ""

        date_m = re.search(
            r'<span[^>]+class="[^"]*date[^"]*"[^>]*>([\s\S]*?)</span>',
            block, re.IGNORECASE,
        )
        posted_date = _clean_text(date_m.group(1)) if date_m else None

        snippet_m = re.search(
            r'<p[^>]+class="[^"]*(?:description|snippet|summary)[^"]*"[^>]*>([\s\S]*?)</p>',
            block, re.IGNORECASE,
        )
        description = _clean_text(snippet_m.group(1)) if snippet_m else ""

        salary = _parse_salary(block)
        work_type = _infer_work_type(title + " " + description + " " + block[:500])

        job_id = hashlib.md5(url.encode()).hexdigest()[:12]
        jobs.append({
            "id": f"jora_{job_id}",
            "title": title[:200],
            "employer": employer[:100],
            "location": location[:100],
            "work_type": work_type,
            "salary": salary,
            "description_snippet": description[:600],
            "source_name": "Jora",
            "source_url": url,
            "official_url": url,
            "posted_date": posted_date[:30] if posted_date else None,
            "closing_date": None,
            "eligibility_notes": None,
        })

    return jobs


class JoraConnector(BaseConnector):
    name = "Jora"

    async def search(
        self,
        query: str,
        location: str,
        radius_km: int = 50,
        work_type: str = "any",
        results_per_page: int = 20,
    ) -> tuple[list[dict], SourceStatus]:
        params: dict = {"q": query, "l": location or "Australia"}
        if work_type == "remote":
            params["q"] = f"{query} remote"

        try:
            async with httpx.AsyncClient(
                timeout=15.0,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/120.0.0.0 Safari/537.36"
                    ),
                    "Accept": "text/html,application/xhtml+xml",
                    "Accept-Language": "en-AU,en;q=0.9",
                },
                follow_redirects=True,
            ) as client:
                resp = await client.get(JORA_SEARCH_URL, params=params)

            if resp.status_code == 200:
                jobs = _parse_jora_html(resp.text, "https://au.jora.com")
                if jobs:
                    return jobs[:results_per_page], SourceStatus(
                        name=self.name,
                        status="available",
                        message=f"Found {len(jobs)} jobs on Jora",
                    )
                return [], SourceStatus(
                    name=self.name,
                    status="limited",
                    message="Jora returned no results for this search",
                )
            elif resp.status_code == 429:
                return [], SourceStatus(
                    name=self.name,
                    status="unavailable",
                    message="Jora rate limit reached — try again in a moment",
                )
            else:
                return [], SourceStatus(
                    name=self.name,
                    status="unavailable",
                    message=f"Jora returned HTTP {resp.status_code}",
                )

        except httpx.TimeoutException:
            logger.warning("Jora request timed out")
            return [], SourceStatus(
                name=self.name,
                status="unavailable",
                message="Jora timed out — try again later",
            )
        except Exception as e:
            logger.error(f"Jora connector error: {e}")
            return [], SourceStatus(
                name=self.name,
                status="unavailable",
                message=f"Jora unavailable: {str(e)[:80]}",
            )
