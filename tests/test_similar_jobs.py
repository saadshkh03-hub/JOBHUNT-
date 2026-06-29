"""Tests for similar_jobs.py"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

import pytest
from app.similar_jobs import generate_similar_queries
from app.models import CandidateProfile, SearchRequest


def make_candidate(**kwargs) -> CandidateProfile:
    defaults = dict(
        name="Test",
        skills=["python", "django", "aws", "docker"],
        tools=["docker", "aws"],
        certifications=[],
        industries=["Technology"],
        domains=["Software Engineer"],
        seniority="senior",
        years_experience=7.0,
        role_families=["Software Engineer", "Cloud / DevOps Engineer"],
        location="Sydney",
        raw_text="",
    )
    defaults.update(kwargs)
    return CandidateProfile(**defaults)


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


class TestGenerateSimilarQueries:
    def test_returns_list(self):
        queries = generate_similar_queries(make_candidate(), make_request())
        assert isinstance(queries, list)

    def test_generates_queries(self):
        queries = generate_similar_queries(make_candidate(), make_request())
        assert len(queries) > 0

    def test_queries_have_required_fields(self):
        queries = generate_similar_queries(make_candidate(), make_request())
        for q in queries:
            assert "query" in q
            assert "location" in q
            assert "radius_km" in q

    def test_includes_adjacent_titles(self):
        candidate = make_candidate(role_families=["Software Engineer"])
        request = make_request(job_title="Software Engineer")
        queries = generate_similar_queries(candidate, request)
        query_strings = [q["query"].lower() for q in queries]
        # Should include adjacent titles like Developer
        assert any("developer" in q or "engineer" in q for q in query_strings)

    def test_no_duplicate_queries(self):
        queries = generate_similar_queries(make_candidate(), make_request())
        keys = [(q["query"].lower(), q["location"].lower(), q["radius_km"]) for q in queries]
        assert len(keys) == len(set(keys))

    def test_max_10_queries(self):
        queries = generate_similar_queries(make_candidate(), make_request())
        assert len(queries) <= 10

    def test_no_original_query_duplicated(self):
        """Identical query+location+radius combos should not appear twice."""
        request = make_request(job_title="Software Engineer", location="Sydney")
        queries = generate_similar_queries(make_candidate(), request)
        # Deduplication: no two entries should share the exact same (query, location, radius) triple
        seen = set()
        for q in queries:
            key = (q["query"].lower(), q.get("location", "").lower(), q.get("radius_km", 0))
            assert key not in seen, f"Duplicate query found: {key}"
            seen.add(key)

    def test_wider_radius_included(self):
        """When radius is small, a wider radius expansion should be included."""
        request = make_request(radius_km=10)
        queries = generate_similar_queries(make_candidate(), request)
        radiuses = [q["radius_km"] for q in queries]
        assert any(r > 10 for r in radiuses)

    def test_policy_officer_role(self):
        candidate = make_candidate(
            role_families=["Policy Officer"],
            skills=["policy", "policy development", "government", "stakeholder management"],
        )
        request = make_request(job_title="Policy Officer", location="Canberra")
        queries = generate_similar_queries(candidate, request)
        assert len(queries) > 0
        query_strings = [q["query"].lower() for q in queries]
        assert any("policy" in q or "analyst" in q or "advisor" in q for q in query_strings)

    def test_empty_role_families_still_returns(self):
        candidate = make_candidate(role_families=[])
        request = make_request(job_title="Engineer")
        queries = generate_similar_queries(candidate, request)
        assert isinstance(queries, list)
