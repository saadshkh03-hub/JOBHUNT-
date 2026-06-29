from __future__ import annotations
import re
import hashlib
from typing import Optional
from .models import JobListing


def _slug(text: str) -> str:
    """Normalize text for comparison."""
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9\s]", "", text.lower())).strip()


def _token_similarity(a: str, b: str) -> float:
    """Jaccard similarity on word tokens."""
    tokens_a = set(_slug(a).split())
    tokens_b = set(_slug(b).split())
    if not tokens_a or not tokens_b:
        return 0.0
    intersection = tokens_a & tokens_b
    union = tokens_a | tokens_b
    return len(intersection) / len(union)


def _safe_str(val, default: str = "") -> str:
    if val is None:
        return default
    return str(val).strip()


def normalize_job(raw: dict) -> JobListing:
    """Convert a raw dict from any connector into a JobListing."""
    title = _safe_str(raw.get("title"), "Untitled Role")
    employer = _safe_str(raw.get("employer") or raw.get("company"), "Unknown Employer")
    location = _safe_str(raw.get("location"), "Australia")
    description = _safe_str(
        raw.get("description_snippet") or raw.get("description") or raw.get("snippet"), ""
    )
    # Trim long descriptions
    if len(description) > 800:
        description = description[:797] + "..."

    source_url = _safe_str(raw.get("source_url") or raw.get("url"), "")
    official_url = _safe_str(raw.get("official_url") or raw.get("apply_url"), "") or None
    if not official_url and source_url:
        official_url = source_url

    work_type = _safe_str(raw.get("work_type") or raw.get("contract_type"), "") or None
    salary = _safe_str(raw.get("salary") or raw.get("salary_min"), "") or None
    if salary == "0" or salary == "0.0":
        salary = None

    posted_date = _safe_str(raw.get("posted_date") or raw.get("created"), "") or None
    closing_date = _safe_str(raw.get("closing_date") or raw.get("expiration_date"), "") or None
    eligibility_notes = _safe_str(raw.get("eligibility_notes"), "") or None

    # Generate a stable ID
    id_source = f"{title}|{employer}|{source_url}"
    job_id = _safe_str(raw.get("id"), "") or hashlib.md5(id_source.encode()).hexdigest()[:12]

    return JobListing(
        id=job_id,
        title=title,
        employer=employer,
        location=location,
        work_type=work_type,
        salary=salary,
        description_snippet=description,
        source_name=_safe_str(raw.get("source_name"), "Unknown"),
        source_url=source_url,
        official_url=official_url,
        posted_date=posted_date,
        closing_date=closing_date,
        eligibility_notes=eligibility_notes,
    )


def deduplicate_jobs(jobs: list[JobListing]) -> list[JobListing]:
    """
    Remove duplicate jobs. Two jobs are duplicates if:
    - title similarity > 85% AND employer similarity > 70%

    When duplicates are found, prefer the one with an official_url.
    """
    if not jobs:
        return []

    kept: list[JobListing] = []

    for candidate in jobs:
        is_dup = False
        for i, existing in enumerate(kept):
            title_sim = _token_similarity(candidate.title, existing.title)
            employer_sim = _token_similarity(candidate.employer, existing.employer)

            if title_sim >= 0.85 and employer_sim >= 0.70:
                is_dup = True
                # Prefer the one with official_url or more info
                if candidate.official_url and not existing.official_url:
                    kept[i] = candidate
                elif (
                    candidate.official_url
                    and existing.official_url
                    and len(candidate.description_snippet) > len(existing.description_snippet)
                ):
                    kept[i] = candidate
                break

        if not is_dup:
            kept.append(candidate)

    return kept
