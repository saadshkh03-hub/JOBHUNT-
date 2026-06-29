from __future__ import annotations
import asyncio
import csv
import io
import logging
import os
import time
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse

from app.models import (
    CandidateProfile,
    SearchRequest,
    SearchResponse,
    ScoredJob,
    SourceStatus,
)
from app.resume_parser import parse_resume
from app.normalizer import normalize_job, deduplicate_jobs
from app.scorer import score_job
from app.similar_jobs import generate_similar_queries
from app.connectors.registry import create_connector_registry, get_active_connectors

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Resume Job Matcher AU", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Build connector registry once at startup
_registry = create_connector_registry(
    adzuna_app_id=os.getenv("ADZUNA_APP_ID"),
    adzuna_app_key=os.getenv("ADZUNA_APP_KEY"),
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    elapsed = time.time() - start
    logger.info(f"{request.method} {request.url.path} → {response.status_code} ({elapsed:.2f}s)")
    return response


@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}


@app.post("/api/resume/parse", response_model=CandidateProfile)
async def parse_resume_endpoint(file: UploadFile = File(...)):
    if not file:
        raise HTTPException(status_code=400, detail="No file provided")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty file")

    content_type = file.content_type or ""
    if not content_type:
        filename = file.filename or ""
        if filename.endswith(".pdf"):
            content_type = "application/pdf"
        elif filename.endswith(".docx"):
            content_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        elif filename.endswith(".doc"):
            content_type = "application/msword"
        else:
            content_type = "text/plain"

    try:
        profile = parse_resume(content, content_type)
        return profile
    except Exception as e:
        logger.error(f"Resume parsing error: {e}", exc_info=True)
        raise HTTPException(status_code=422, detail=f"Failed to parse resume: {str(e)}")


async def _run_connector_search(
    connector,
    query: str,
    location: str,
    radius_km: int,
    work_type: str,
) -> tuple[list[dict], SourceStatus]:
    """Run a single connector search with timeout protection."""
    try:
        return await asyncio.wait_for(
            connector.search(
                query=query,
                location=location,
                radius_km=radius_km,
                work_type=work_type,
                results_per_page=20,
            ),
            timeout=20.0,
        )
    except asyncio.TimeoutError:
        return [], SourceStatus(
            name=connector.name,
            status="unavailable",
            message=f"{connector.name} timed out after 20s",
        )
    except Exception as e:
        logger.error(f"Connector {connector.name} error: {e}")
        return [], SourceStatus(
            name=connector.name,
            status="unavailable",
            message=f"{connector.name} error: {str(e)[:80]}",
        )


async def _gather_jobs(
    connectors,
    query: str,
    location: str,
    radius_km: int,
    work_type: str,
) -> tuple[list[dict], list[SourceStatus]]:
    """Run all connectors concurrently and aggregate results."""
    tasks = [
        _run_connector_search(c, query, location, radius_km, work_type)
        for c in connectors
    ]
    results = await asyncio.gather(*tasks)

    all_jobs: list[dict] = []
    statuses: list[SourceStatus] = []
    for jobs, status in results:
        all_jobs.extend(jobs)
        statuses.append(status)

    return all_jobs, statuses


def _build_search_request_from_form(
    job_title: str,
    location: str,
    radius_km: int,
    work_type: str,
    job_source_filter: str,
    min_score: int,
    strong_match_threshold: int,
    min_strong_matches: int,
) -> SearchRequest:
    return SearchRequest(
        job_title=job_title,
        location=location,
        radius_km=radius_km,
        work_type=work_type,  # type: ignore[arg-type]
        job_source_filter=job_source_filter,  # type: ignore[arg-type]
        min_score=min_score,
        strong_match_threshold=strong_match_threshold,
        min_strong_matches=min_strong_matches,
    )


@app.post("/api/search", response_model=SearchResponse)
async def search_jobs(
    file: UploadFile = File(...),
    job_title: str = Form(default=""),
    location: str = Form(default=""),
    radius_km: int = Form(default=50),
    work_type: str = Form(default="any"),
    job_source_filter: str = Form(default="all"),
    min_score: int = Form(default=40),
    strong_match_threshold: int = Form(default=70),
    min_strong_matches: int = Form(default=5),
):
    # 1. Parse resume
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty resume file")

    content_type = file.content_type or ""
    if not content_type:
        filename = file.filename or ""
        if filename.endswith(".pdf"):
            content_type = "application/pdf"
        elif filename.endswith(".docx"):
            content_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        else:
            content_type = "text/plain"

    try:
        candidate = parse_resume(content, content_type)
    except Exception as e:
        logger.error(f"Resume parsing error: {e}")
        raise HTTPException(status_code=422, detail=f"Failed to parse resume: {str(e)}")

    search_request = _build_search_request_from_form(
        job_title=job_title,
        location=location,
        radius_km=radius_km,
        work_type=work_type,
        job_source_filter=job_source_filter,
        min_score=min_score,
        strong_match_threshold=strong_match_threshold,
        min_strong_matches=min_strong_matches,
    )

    # Use candidate location if not specified
    effective_location = location or candidate.location or "Australia"
    effective_query = job_title or (candidate.role_families[0] if candidate.role_families else "")

    # 2. Get active connectors
    connectors = get_active_connectors(_registry, job_source_filter)

    # 3. Run all connectors concurrently
    raw_jobs, statuses = await _gather_jobs(
        connectors,
        query=effective_query,
        location=effective_location,
        radius_km=radius_km,
        work_type=work_type,
    )

    # 4. Normalize
    normalized = []
    for raw in raw_jobs:
        try:
            normalized.append(normalize_job(raw))
        except Exception as e:
            logger.debug(f"Normalize error: {e}")

    # 5. Deduplicate
    deduped = deduplicate_jobs(normalized)
    total_fetched = len(deduped)

    # 6. Score each job
    scored: list[ScoredJob] = []
    for job in deduped:
        try:
            scored_job = score_job(job, candidate, search_request)
            scored.append(scored_job)
        except Exception as e:
            logger.debug(f"Scoring error for {job.title}: {e}")

    # 7. Sort: eligibility_fit DESC, score DESC
    scored.sort(key=lambda j: (j.score_breakdown.eligibility_fit, j.score), reverse=True)

    # 8. Split into strong_matches and others
    strong_matches = [
        j for j in scored
        if j.is_strong_match and j.score >= min_score
    ]
    other_matches = [
        j for j in scored
        if not j.is_strong_match and j.score >= min_score
    ]

    search_expanded = False

    # 9. Expand search if not enough strong matches
    if len(strong_matches) < min_strong_matches and effective_query:
        similar_queries = generate_similar_queries(candidate, search_request)
        for sq in similar_queries[:5]:
            if len(strong_matches) >= min_strong_matches:
                break
            try:
                extra_raw, extra_status = await _gather_jobs(
                    connectors,
                    query=sq["query"],
                    location=sq.get("location", effective_location),
                    radius_km=sq.get("radius_km", radius_km),
                    work_type=work_type,
                )
                extra_normalized = []
                for raw in extra_raw:
                    try:
                        extra_normalized.append(normalize_job(raw))
                    except Exception:
                        pass

                extra_deduped = deduplicate_jobs(extra_normalized)
                # Remove already-seen jobs
                existing_ids = {j.id for j in scored}

                for job in extra_deduped:
                    if job.id in existing_ids:
                        continue
                    try:
                        sj = score_job(job, candidate, search_request)
                        sj.is_similar_job = True
                        if sj.score >= min_score:
                            other_matches.append(sj)
                            if sj.is_strong_match:
                                strong_matches.append(sj)
                        existing_ids.add(job.id)
                        search_expanded = True
                    except Exception:
                        pass
            except Exception as e:
                logger.debug(f"Expansion search error: {e}")

    # Mark similar jobs in other_matches
    for j in other_matches:
        j.is_similar_job = True

    # Final sort
    strong_matches.sort(key=lambda j: (j.score_breakdown.eligibility_fit, j.score), reverse=True)
    other_matches.sort(key=lambda j: j.score, reverse=True)

    message = None
    if not strong_matches and not other_matches:
        message = "No jobs found. Try broadening your search location, radius, or lowering the minimum score."
    elif search_expanded:
        message = f"Search expanded to find similar roles. {len(strong_matches)} strong matches found."

    return SearchResponse(
        strong_matches=strong_matches[:50],
        similar_jobs=other_matches[:50],
        sources=statuses,
        total_fetched=total_fetched,
        search_expanded=search_expanded,
        message=message,
    )


# ── CSV Export ─────────────────────────────────────────────────────────────

@app.post("/api/export/csv")
async def export_csv(payload: dict):
    """
    Accept a JSON body with {"jobs": [...ScoredJob dicts...]} and return a CSV file.
    """
    jobs = payload.get("jobs", [])
    if not jobs:
        raise HTTPException(status_code=400, detail="No jobs provided for export")

    fieldnames = [
        "score", "match_type", "title", "employer", "location", "work_type",
        "salary", "source_name", "posted_date", "closing_date",
        "explanation", "blockers", "missing_skills", "application_url",
    ]

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()

    for job in jobs:
        writer.writerow({
            "score": job.get("score", ""),
            "match_type": "Strong Match" if job.get("is_strong_match") else "Similar Job",
            "title": job.get("title", ""),
            "employer": job.get("employer", ""),
            "location": job.get("location", ""),
            "work_type": job.get("work_type", ""),
            "salary": job.get("salary", ""),
            "source_name": job.get("source_name", ""),
            "posted_date": job.get("posted_date", ""),
            "closing_date": job.get("closing_date", ""),
            "explanation": " | ".join(job.get("explanation", [])),
            "blockers": " | ".join(job.get("blockers", [])),
            "missing_skills": ", ".join(job.get("missing_skills", [])),
            "application_url": job.get("official_url") or job.get("source_url", ""),
        })

    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8")),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=job-matches.csv"},
    )


# ── AI Assist: Cover Letter & Resume Tailoring ──────────────────────────────

from pydantic import BaseModel as _BaseModel


class AssistRequest(_BaseModel):
    action: str
    job_title: str
    employer: str
    job_description: str
    candidate_summary: str
    candidate_skills: list[str]
    candidate_role_families: list[str]


class AssistResponse(_BaseModel):
    action: str
    content: str


@app.post("/api/assist", response_model=AssistResponse)
async def assist(req: AssistRequest):
    """
    Generate a cover letter starter or resume tailoring suggestions without
    relying on an external LLM — produces template-based but personalised output.
    """
    skills_str = ", ".join(req.candidate_skills[:8]) if req.candidate_skills else "various professional skills"
    role_str = req.candidate_role_families[0] if req.candidate_role_families else "professional"

    # Extract key terms from the job description
    desc_lower = req.job_description.lower()
    matched_skills = [s for s in req.candidate_skills if s.lower() in desc_lower][:5]
    matched_str = ", ".join(matched_skills) if matched_skills else skills_str

    if req.action == "cover_letter":
        content = f"""Dear Hiring Manager,

I am writing to express my strong interest in the {req.job_title} position at {req.employer}.

{req.candidate_summary.strip() if req.candidate_summary else f"As an experienced {role_str}, I bring a solid foundation of skills and a track record of delivering results."}

My background includes expertise in {matched_str}, which aligns directly with the requirements outlined in your advertisement. I am confident that my experience in {role_str.lower()} would allow me to contribute meaningfully to your team from day one.

I am particularly drawn to this opportunity at {req.employer} because it offers the chance to apply my skills in a meaningful way and continue growing as a {role_str.lower()}.

I would welcome the opportunity to discuss how my background and capabilities align with your needs. Thank you for considering my application.

Yours sincerely,
[Your Name]

---
Note: This is a starter draft — personalise it with specific achievements and tailor it further to the role before submitting.
"""

    elif req.action == "tailor_resume":
        # Extract likely keywords from description
        keyword_patterns = [
            r'\b([A-Z][a-z]+(?:\s[A-Z][a-z]+)*)\b',
        ]
        jd_words = set(re.findall(r'\b[a-zA-Z]{4,}\b', req.job_description))
        resume_words = set(re.findall(r'\b[a-zA-Z]{4,}\b', req.candidate_summary))
        missing_keywords = [w for w in jd_words if w not in resume_words and len(w) > 5][:8]

        content = f"""Resume Tailoring Suggestions for: {req.job_title} at {req.employer}

── Summary Line ─────────────────────────────────────────────────────
Consider opening your resume summary with something like:
"Experienced {role_str} with expertise in {matched_str}, seeking to contribute to {req.employer}."

── Skills to Highlight ──────────────────────────────────────────────
Your resume already shows: {matched_str}

These skills from the job description would strengthen your application if added or made more prominent:
{chr(10).join(f'• {kw}' for kw in missing_keywords) if missing_keywords else '• Your current skills appear well-aligned — ensure they are clearly listed near the top'}

── Bullet Point Tips ────────────────────────────────────────────────
• Quantify achievements where possible (e.g. "Reduced processing time by 30%")
• Mirror terminology from the job description in your experience bullets
• Lead with action verbs: Delivered, Led, Designed, Developed, Managed

── Keywords to Weave In ─────────────────────────────────────────────
{', '.join(missing_keywords[:6]) if missing_keywords else 'Your resume keywords appear well-matched to this role'}

── Format Reminders ─────────────────────────────────────────────────
• Keep resume to 2 pages maximum for this seniority level
• List your most relevant experience first
• Ensure contact details are current and professional

---
Note: These are automated suggestions — review each point in context of your actual experience.
"""
    else:
        raise HTTPException(status_code=400, detail=f"Unknown action: {req.action}")

    return AssistResponse(action=req.action, content=content)
