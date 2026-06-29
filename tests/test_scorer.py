"""Tests for scorer.py"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

import pytest
from app.scorer import score_job, check_eligibility, score_location_fit, score_work_type_fit
from app.models import CandidateProfile, JobListing, SearchRequest, ScoredJob


def make_candidate(**kwargs) -> CandidateProfile:
    defaults = dict(
        name="Test Candidate",
        skills=["python", "django", "react", "aws", "docker", "sql", "agile"],
        tools=["docker", "aws", "git"],
        certifications=["AWS Certified Developer"],
        industries=["Technology"],
        domains=["Software Engineer"],
        seniority="senior",
        years_experience=8.0,
        role_families=["Software Engineer", "Cloud / DevOps Engineer"],
        location="Sydney",
        raw_text="",
    )
    defaults.update(kwargs)
    return CandidateProfile(**defaults)


def make_job(**kwargs) -> JobListing:
    defaults = dict(
        id="job1",
        title="Senior Software Engineer",
        employer="Tech Co",
        location="Sydney, NSW",
        work_type="hybrid",
        salary="$120,000 – $150,000",
        description_snippet="We need a Senior Software Engineer with Python, Django, AWS experience. "
                            "Agile environment. SQL required. Docker and Kubernetes a plus.",
        source_name="Adzuna",
        source_url="https://example.com/job1",
        official_url="https://example.com/job1",
        posted_date="2024-01-15",
        closing_date=None,
        eligibility_notes=None,
    )
    defaults.update(kwargs)
    return JobListing(**defaults)


def make_request(**kwargs) -> SearchRequest:
    defaults = dict(
        job_title="Software Engineer",
        location="Sydney",
        radius_km=50,
        work_type="any",
        job_source_filter="all",
        min_score=40,
        strong_match_threshold=70,
        min_strong_matches=5,
    )
    defaults.update(kwargs)
    return SearchRequest(**defaults)


class TestScoreJob:
    def test_returns_scored_job(self):
        job = make_job()
        candidate = make_candidate()
        request = make_request()
        result = score_job(job, candidate, request)
        assert isinstance(result, ScoredJob)

    def test_perfect_match_scores_high(self):
        job = make_job()
        candidate = make_candidate()
        request = make_request()
        result = score_job(job, candidate, request)
        assert result.score >= 60, f"Expected score >=60, got {result.score}"

    def test_mismatch_scores_low(self):
        job = make_job(
            title="Accountant",
            description_snippet="We need a qualified accountant with MYOB, Xero, tax experience, CPA.",
        )
        candidate = make_candidate(
            skills=["python", "machine learning", "tensorflow"],
            role_families=["Data Scientist"],
        )
        request = make_request(job_title="Data Scientist")
        result = score_job(job, candidate, request)
        assert result.score < 70, f"Expected score <70, got {result.score}"

    def test_strong_match_flagged_correctly(self):
        job = make_job()
        candidate = make_candidate()
        request = make_request(strong_match_threshold=60)
        result = score_job(job, candidate, request)
        # With a good match and threshold of 60, should be strong
        if result.score >= 60 and not result.blockers:
            assert result.is_strong_match

    def test_citizenship_blocker(self):
        job = make_job(
            description_snippet="Must be an Australian citizen. Security clearance required.",
            eligibility_notes="Australian citizenship required.",
        )
        candidate = make_candidate()
        request = make_request()
        result = score_job(job, candidate, request)
        assert len(result.blockers) > 0
        assert not result.is_strong_match  # Blockers prevent strong match

    def test_security_clearance_blocker(self):
        job = make_job(description_snippet="NV1 security clearance required for this APS role.")
        result = score_job(job, make_candidate(), make_request())
        assert any("clearance" in b.lower() for b in result.blockers)

    def test_remote_job_location_fit(self):
        job = make_job(
            location="Remote",
            work_type="remote",
            description_snippet="Fully remote Python developer role.",
        )
        candidate = make_candidate(location="Brisbane")
        request = make_request(location="Brisbane")
        result = score_job(job, candidate, request)
        assert result.score_breakdown.location_fit == 100.0

    def test_work_type_mismatch_reduces_score(self):
        job_remote = make_job(work_type="remote", description_snippet="Remote only role. Python Django required.")
        job_onsite = make_job(work_type="onsite", description_snippet="On-site role in office. Python Django required.")
        candidate = make_candidate()
        request_remote = make_request(work_type="remote")
        request_onsite = make_request(work_type="onsite")

        score_remote_match = score_job(job_remote, candidate, request_remote).score_breakdown.work_type_fit
        score_remote_mismatch = score_job(job_onsite, candidate, request_remote).score_breakdown.work_type_fit

        assert score_remote_match >= score_remote_mismatch

    def test_score_has_breakdown(self):
        result = score_job(make_job(), make_candidate(), make_request())
        bd = result.score_breakdown
        assert bd.title_relevance >= 0
        assert bd.skills_overlap >= 0
        assert bd.location_fit >= 0

    def test_score_never_crashes_on_none_fields(self):
        job = make_job(
            work_type=None,
            salary=None,
            description_snippet="",
            eligibility_notes=None,
            closing_date=None,
            posted_date=None,
        )
        candidate = make_candidate(
            skills=[],
            tools=[],
            certifications=[],
            industries=[],
            role_families=[],
            location="",
        )
        request = make_request(job_title="", location="")
        # Should not raise
        result = score_job(job, candidate, request)
        assert 0 <= result.score <= 100

    def test_explanation_has_items(self):
        job = make_job()
        result = score_job(job, make_candidate(), make_request())
        assert isinstance(result.explanation, list)

    def test_explanation_max_4_items(self):
        job = make_job()
        result = score_job(job, make_candidate(), make_request())
        assert len(result.explanation) <= 4


class TestCheckEligibility:
    def test_no_blockers_for_plain_job(self):
        job = make_job(description_snippet="Great Python role at a startup. Agile team.")
        score, blockers = check_eligibility(job)
        assert score == 100.0
        assert blockers == []

    def test_citizenship_detected(self):
        job = make_job(description_snippet="Must be an Australian citizen to apply.")
        score, blockers = check_eligibility(job)
        assert len(blockers) > 0

    def test_clearance_detected(self):
        job = make_job(description_snippet="Top secret security clearance required.")
        _, blockers = check_eligibility(job)
        assert len(blockers) > 0


class TestLocationFit:
    def test_remote_always_100(self):
        job = make_job(location="Remote", work_type="remote")
        candidate = make_candidate(location="Darwin")
        request = make_request(location="Perth")
        score = score_location_fit(job, candidate, request)
        assert score == 100.0

    def test_same_city_100(self):
        job = make_job(location="Sydney, NSW")
        candidate = make_candidate(location="Sydney")
        request = make_request(location="Sydney")
        score = score_location_fit(job, candidate, request)
        assert score == 100.0

    def test_different_city_lower(self):
        job = make_job(location="Perth, WA")
        candidate = make_candidate(location="Sydney")
        request = make_request(location="Sydney", radius_km=50)
        score = score_location_fit(job, candidate, request)
        assert score < 100.0
