from __future__ import annotations
import re
from typing import Optional
from .models import CandidateProfile, JobListing, ScoredJob, ScoreBreakdown, SearchRequest

# Weights must total 100
WEIGHTS = {
    "title_relevance": 20,
    "skills_overlap": 25,
    "preferred_skills": 10,
    "seniority_alignment": 10,
    "industry_relevance": 10,
    "location_fit": 10,
    "work_type_fit": 5,
    "eligibility_fit": 5,
    "transferable_skills": 5,
}

SENIORITY_LEVELS = {
    "intern": 0, "cadet": 0, "trainee": 0,
    "junior": 1, "graduate": 1, "entry": 1, "associate": 1,
    "mid": 2, "intermediate": 2, "analyst": 2,
    "senior": 3, "sr": 3, "experienced": 3, "principal": 3, "staff": 3,
    "lead": 4, "tech lead": 4, "team lead": 4,
    "manager": 5, "head": 5, "director": 5,
    "executive": 6, "vp": 6, "chief": 6, "cto": 6, "ceo": 6,
}

# Only flag truly hard citizenship requirements (not general "working rights" phrases)
CITIZENSHIP_PATTERNS = [
    r"must\s+be\s+(?:an?\s+)?australian\s+citizen",
    r"australian\s+citizen(?:ship)?\s+(?:is\s+)?(?:required|mandatory|essential|only)",
    r"citizenship\s+(?:is\s+)?(?:required|mandatory|essential)",
    r"(?:only\s+)?australian\s+citizens?\s+(?:are\s+)?(?:eligible|may\s+apply)",
    r"candidates?\s+must\s+hold\s+australian\s+citizenship",
]

CLEARANCE_PATTERNS = [
    r"security\s+clearance",
    r"nv1|nv2|pv\s+clearance",
    r"baseline\s+clearance",
    r"top\s+secret",
    r"secret\s+clearance",
    r"government\s+(?:security\s+)?clearance",
]

# Common skills to look for in job descriptions
COMMON_REQUIRED_SKILLS = {
    "python", "java", "javascript", "typescript", "sql", "react", "angular",
    "vue", "node.js", "aws", "azure", "gcp", "docker", "kubernetes",
    "machine learning", "data analysis", "agile", "scrum", "project management",
    "excel", "power bi", "tableau", "salesforce", "sap", "jira",
    "communication", "stakeholder management", "leadership", "management",
    "financial analysis", "accounting", "marketing", "recruitment",
    "policy", "research", "analysis", "writing", "presentation",
    "c#", "c++", "ruby", "go", "rust", "scala", "r",
    "django", "flask", "fastapi", "spring", "express",
    "postgresql", "mysql", "mongodb", "redis", "elasticsearch",
    "terraform", "ansible", "jenkins", "ci/cd",
    "figma", "sketch", "ux", "ui",
    "cybersecurity", "information security",
}


def _normalize(text: Optional[str]) -> str:
    if not text:
        return ""
    return text.lower().strip()


def _jaccard_similarity(set_a: set, set_b: set) -> float:
    if not set_a or not set_b:
        return 0.0
    intersection = set_a & set_b
    union = set_a | set_b
    return len(intersection) / len(union)


def _token_overlap(text_a: str, text_b: str) -> float:
    """Simple token overlap between two strings."""
    tokens_a = set(re.findall(r"\b\w+\b", text_a.lower()))
    tokens_b = set(re.findall(r"\b\w+\b", text_b.lower()))
    if not tokens_a or not tokens_b:
        return 0.0
    return len(tokens_a & tokens_b) / max(len(tokens_a), len(tokens_b))


def score_title_relevance(
    job: JobListing, candidate: CandidateProfile, search_request: SearchRequest
) -> float:
    job_title = _normalize(job.title)
    search_title = _normalize(search_request.job_title)
    role_families_text = " ".join(candidate.role_families).lower()

    score = 0.0

    # Direct match with search title
    if search_title and search_title in job_title:
        score = max(score, 90.0)
    elif search_title:
        overlap = _token_overlap(search_title, job_title)
        score = max(score, overlap * 80.0)

    # Match against role families
    for family in candidate.role_families:
        family_tokens = set(re.findall(r"\b\w+\b", family.lower()))
        job_tokens = set(re.findall(r"\b\w+\b", job_title))
        if family_tokens & job_tokens:
            family_score = (len(family_tokens & job_tokens) / max(len(family_tokens), 1)) * 75.0
            score = max(score, family_score)

    # Keyword in job description
    if search_title:
        desc = _normalize(job.description_snippet)
        if search_title in desc:
            score = max(score, 50.0)

    return min(score, 100.0)


def extract_required_skills_from_job(job: JobListing) -> set[str]:
    """Extract required skills mentioned in the job description."""
    combined = f"{job.title} {job.description_snippet} {job.eligibility_notes or ''}".lower()
    found = set()
    for skill in COMMON_REQUIRED_SKILLS:
        pattern = r"(?<![a-z0-9])" + re.escape(skill) + r"(?![a-z0-9])"
        if re.search(pattern, combined):
            found.add(skill)
    return found


def score_skills_overlap(
    job: JobListing, candidate: CandidateProfile
) -> tuple[float, list[str]]:
    """Returns score 0-100 and list of missing skills."""
    required_skills = extract_required_skills_from_job(job)
    if not required_skills:
        return 50.0, []  # Can't assess, give benefit of doubt

    candidate_skills = {s.lower() for s in candidate.skills}
    matched = required_skills & candidate_skills
    missing = list(required_skills - candidate_skills)

    if not required_skills:
        return 50.0, []

    coverage = len(matched) / len(required_skills)
    score = coverage * 100.0
    return score, missing[:5]


def score_preferred_skills(job: JobListing, candidate: CandidateProfile) -> float:
    """Score based on having skills beyond the minimum required."""
    combined = f"{job.title} {job.description_snippet}".lower()
    candidate_skills = {s.lower() for s in candidate.skills}

    # Look for "preferred", "desirable", "bonus" skills
    preferred_section = ""
    pref_pattern = r"(?i)(?:preferred|desirable|bonus|nice.to.have|advantageous)[:\s]+([\s\S]{0,300})"
    m = re.search(pref_pattern, combined)
    if m:
        preferred_section = m.group(1)

    if not preferred_section:
        # Use tools overlap as proxy
        job_tools_mentioned = {s for s in COMMON_REQUIRED_SKILLS if s in combined}
        if not job_tools_mentioned:
            return 50.0
        matched = job_tools_mentioned & candidate_skills
        return (len(matched) / max(len(job_tools_mentioned), 1)) * 70.0

    pref_skills = set()
    for skill in COMMON_REQUIRED_SKILLS:
        if skill in preferred_section:
            pref_skills.add(skill)

    if not pref_skills:
        return 50.0
    matched = pref_skills & candidate_skills
    return (len(matched) / len(pref_skills)) * 100.0


def infer_job_seniority(job: JobListing) -> int:
    """Infer seniority level of a job posting (0-6 scale)."""
    combined = f"{job.title} {job.description_snippet}".lower()
    best_level = 2  # default mid
    best_score = -1

    for keyword, level in SENIORITY_LEVELS.items():
        if re.search(r"\b" + re.escape(keyword) + r"\b", combined):
            if level > best_score:
                best_score = level
                best_level = level

    return best_level


def score_seniority_alignment(job: JobListing, candidate: CandidateProfile) -> float:
    candidate_seniority_map = {
        "intern": 0, "cadet": 0, "trainee": 0,
        "junior": 1,
        "mid": 2,
        "senior": 3,
        "lead": 4,
        "manager": 5,
        "executive": 6,
    }
    candidate_level = candidate_seniority_map.get(candidate.seniority, 2)
    job_level = infer_job_seniority(job)

    diff = abs(candidate_level - job_level)
    if diff == 0:
        return 100.0
    elif diff == 1:
        return 70.0
    elif diff == 2:
        return 40.0
    else:
        return 10.0


def score_industry_relevance(job: JobListing, candidate: CandidateProfile) -> float:
    if not candidate.industries:
        return 50.0  # benefit of doubt

    combined = f"{job.title} {job.employer} {job.description_snippet}".lower()
    from .resume_parser import INDUSTRY_KEYWORDS
    for industry in candidate.industries:
        keywords = INDUSTRY_KEYWORDS.get(industry, [])
        for kw in keywords:
            if kw in combined:
                return 100.0

    # Partial overlap
    candidate_domain_words = set()
    for ind in candidate.industries:
        candidate_domain_words.update(ind.lower().split())

    job_words = set(re.findall(r"\b\w+\b", combined))
    overlap = len(candidate_domain_words & job_words)
    if overlap > 0:
        return 60.0
    return 20.0


def score_location_fit(
    job: JobListing, candidate: CandidateProfile, search_request: SearchRequest
) -> float:
    job_loc = _normalize(job.location)
    search_loc = _normalize(search_request.location)
    candidate_loc = _normalize(candidate.location)

    # Remote jobs are always 100
    if any(kw in job_loc for kw in ["remote", "work from home", "wfh", "anywhere"]):
        return 100.0
    if job.work_type and "remote" in job.work_type.lower():
        return 100.0

    # No location specified → be lenient
    if not search_loc:
        return 70.0

    # Exact match
    if search_loc in job_loc or job_loc in search_loc:
        return 100.0

    # State match
    aus_states = {"nsw", "vic", "qld", "wa", "sa", "tas", "nt", "act"}
    job_tokens = set(job_loc.split())
    search_tokens = set(search_loc.split())
    if job_tokens & search_tokens & aus_states:
        return 80.0

    # Candidate location match
    if candidate_loc and (candidate_loc.lower() in job_loc or job_loc in candidate_loc.lower()):
        return 90.0

    # National/Australia-wide
    if "australia" in job_loc or "nationwide" in job_loc or "national" in job_loc:
        return 80.0

    # Radius-based score (approximate)
    radius = search_request.radius_km
    if radius >= 100:
        return 50.0
    return 25.0


def score_work_type_fit(job: JobListing, search_request: SearchRequest) -> float:
    requested = search_request.work_type.lower()
    if requested == "any":
        return 100.0

    job_wt = _normalize(job.work_type or "")
    desc = _normalize(job.description_snippet)

    # Map job work_type to simple categories
    if "remote" in job_wt or "remote" in desc:
        job_type = "remote"
    elif "hybrid" in job_wt or "hybrid" in desc:
        job_type = "hybrid"
    elif "onsite" in job_wt or "on-site" in job_wt or "in office" in desc or "on site" in desc:
        job_type = "onsite"
    else:
        # Unknown → partial credit
        return 60.0

    if job_type == requested:
        return 100.0
    # Close match: hybrid <-> remote or hybrid <-> onsite
    if {job_type, requested} in [{"hybrid", "remote"}, {"hybrid", "onsite"}]:
        return 60.0
    return 20.0


def check_eligibility(job: JobListing) -> tuple[float, list[str]]:
    """
    Returns eligibility score 0-100 and list of blockers.
    Only flags hard mandatory requirements that are clearly stated.
    Uses eligibility_notes as the definitive field; falls back to description.
    """
    blockers = []

    # Prefer eligibility_notes for definitive requirements
    notes = (job.eligibility_notes or "").lower()
    description = (job.description_snippet or "").lower()

    # Hard citizenship check — use notes first, then description patterns
    citizenship_flagged = False
    if notes and ("australian citizen" in notes and "required" in notes):
        citizenship_flagged = True
    if not citizenship_flagged:
        for pattern in CITIZENSHIP_PATTERNS:
            if re.search(pattern, description):
                citizenship_flagged = True
                break
    if citizenship_flagged:
        blockers.append("Australian citizenship required — verify your eligibility")

    # Security clearance check
    clearance_flagged = False
    if notes and ("clearance" in notes or "nv1" in notes or "nv2" in notes):
        clearance_flagged = True
    if not clearance_flagged:
        for pattern in CLEARANCE_PATTERNS:
            if re.search(pattern, description):
                clearance_flagged = True
                break
    if clearance_flagged:
        blockers.append("Security clearance required — check requirements")

    if not blockers:
        return 100.0, []
    # Partial score — flagged but not zero (may still be worth applying)
    return 50.0, blockers


def score_transferable_skills(job: JobListing, candidate: CandidateProfile) -> float:
    """Score for transferable/soft skills."""
    transferable = {
        "communication", "leadership", "teamwork", "collaboration",
        "problem solving", "critical thinking", "adaptability",
        "time management", "organisation", "attention to detail",
        "presentation", "writing", "research", "analysis",
        "stakeholder management", "negotiation", "mentoring",
    }
    candidate_skills_lower = {s.lower() for s in candidate.skills}
    job_text = f"{job.title} {job.description_snippet}".lower()

    job_transferable = {s for s in transferable if s in job_text}
    if not job_transferable:
        return 70.0  # benefit of doubt

    candidate_transferable = transferable & candidate_skills_lower
    matched = job_transferable & candidate_transferable
    return (len(matched) / max(len(job_transferable), 1)) * 100.0


def build_explanations(
    breakdown: ScoreBreakdown,
    job: JobListing,
    candidate: CandidateProfile,
    missing_skills: list[str],
    blockers: list[str],
) -> list[str]:
    explanations = []

    if breakdown.title_relevance >= 70:
        explanations.append(f"Strong title match: '{job.title}' aligns with your experience")
    elif breakdown.title_relevance >= 40:
        explanations.append(f"Partial title match with your background")

    if breakdown.skills_overlap >= 70:
        explanations.append("Your skills closely match the job requirements")
    elif breakdown.skills_overlap >= 40:
        explanations.append("You have several relevant skills for this role")

    if breakdown.seniority_alignment >= 80:
        explanations.append(f"Role seniority matches your {candidate.seniority}-level experience")

    if breakdown.location_fit == 100.0:
        if job.work_type and "remote" in job.work_type.lower():
            explanations.append("Remote work available")
        else:
            explanations.append("Job is in your preferred location")

    if breakdown.industry_relevance >= 80:
        explanations.append(f"Industry aligns with your background ({', '.join(candidate.industries[:2])})")

    if breakdown.eligibility_fit == 100.0 and not blockers:
        explanations.append("No eligibility blockers identified")

    if candidate.years_experience > 0 and breakdown.seniority_alignment >= 60:
        yrs = int(candidate.years_experience)
        if yrs > 0:
            explanations.append(f"Your {yrs}+ years of experience suits this role")

    return explanations[:4]


def score_job(
    job: JobListing,
    candidate: CandidateProfile,
    search_request: SearchRequest,
) -> ScoredJob:
    # Calculate each dimension
    tr = score_title_relevance(job, candidate, search_request)
    so, missing_skills = score_skills_overlap(job, candidate)
    ps = score_preferred_skills(job, candidate)
    sa = score_seniority_alignment(job, candidate)
    ir = score_industry_relevance(job, candidate)
    lf = score_location_fit(job, candidate, search_request)
    wt = score_work_type_fit(job, search_request)
    ef, blockers = check_eligibility(job)
    ts = score_transferable_skills(job, candidate)

    breakdown = ScoreBreakdown(
        title_relevance=round(tr, 1),
        skills_overlap=round(so, 1),
        preferred_skills=round(ps, 1),
        seniority_alignment=round(sa, 1),
        industry_relevance=round(ir, 1),
        location_fit=round(lf, 1),
        work_type_fit=round(wt, 1),
        eligibility_fit=round(ef, 1),
        transferable_skills=round(ts, 1),
    )

    # Weighted total
    total = (
        tr * WEIGHTS["title_relevance"] / 100
        + so * WEIGHTS["skills_overlap"] / 100
        + ps * WEIGHTS["preferred_skills"] / 100
        + sa * WEIGHTS["seniority_alignment"] / 100
        + ir * WEIGHTS["industry_relevance"] / 100
        + lf * WEIGHTS["location_fit"] / 100
        + wt * WEIGHTS["work_type_fit"] / 100
        + ef * WEIGHTS["eligibility_fit"] / 100
        + ts * WEIGHTS["transferable_skills"] / 100
    )
    total = round(min(max(total, 0.0), 100.0), 1)

    explanations = build_explanations(breakdown, job, candidate, missing_skills, blockers)

    # Strong match: score above threshold AND no critical blockers
    is_strong = (
        total >= search_request.strong_match_threshold
        and len(blockers) == 0
    )

    job_data = job.model_dump()
    return ScoredJob(
        **job_data,
        score=total,
        score_breakdown=breakdown,
        explanation=explanations,
        blockers=blockers,
        missing_skills=missing_skills,
        is_strong_match=is_strong,
        is_similar_job=False,
    )
