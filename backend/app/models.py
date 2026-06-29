from __future__ import annotations
from typing import List, Optional, Literal
from pydantic import BaseModel, Field


class CandidateProfile(BaseModel):
    name: str = ""
    summary: str = ""
    skills: List[str] = Field(default_factory=list)
    tools: List[str] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)
    industries: List[str] = Field(default_factory=list)
    domains: List[str] = Field(default_factory=list)
    seniority: str = "mid"  # junior, mid, senior, lead, manager, executive
    years_experience: float = 0.0
    role_families: List[str] = Field(default_factory=list)
    location: str = ""
    raw_text: str = ""


class JobListing(BaseModel):
    id: str
    title: str
    employer: str
    location: str
    work_type: Optional[str] = None
    salary: Optional[str] = None
    description_snippet: str = ""
    source_name: str
    source_url: str
    official_url: Optional[str] = None
    posted_date: Optional[str] = None
    closing_date: Optional[str] = None
    eligibility_notes: Optional[str] = None


class SourceStatus(BaseModel):
    name: str
    status: Literal["available", "limited", "unavailable"]
    message: Optional[str] = None


class ScoreBreakdown(BaseModel):
    title_relevance: float = 0.0
    skills_overlap: float = 0.0
    preferred_skills: float = 0.0
    seniority_alignment: float = 0.0
    industry_relevance: float = 0.0
    location_fit: float = 0.0
    work_type_fit: float = 0.0
    eligibility_fit: float = 0.0
    transferable_skills: float = 0.0


class ScoredJob(JobListing):
    score: float = Field(ge=0.0, le=100.0)
    score_breakdown: ScoreBreakdown = Field(default_factory=ScoreBreakdown)
    explanation: List[str] = Field(default_factory=list)
    blockers: List[str] = Field(default_factory=list)
    missing_skills: List[str] = Field(default_factory=list)
    is_strong_match: bool = False
    is_similar_job: bool = False


class SearchRequest(BaseModel):
    job_title: str = ""
    location: str = ""
    radius_km: int = 50
    work_type: Literal["any", "onsite", "hybrid", "remote"] = "any"
    job_source_filter: Literal["all", "government", "council"] = "all"
    min_score: int = 40
    strong_match_threshold: int = 70
    min_strong_matches: int = 5


class SearchResponse(BaseModel):
    strong_matches: List[ScoredJob] = Field(default_factory=list)
    similar_jobs: List[ScoredJob] = Field(default_factory=list)
    sources: List[SourceStatus] = Field(default_factory=list)
    total_fetched: int = 0
    search_expanded: bool = False
    message: Optional[str] = None
