"""Tests for normalizer.py"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

import pytest
from app.normalizer import normalize_job, deduplicate_jobs
from app.models import JobListing


def make_raw(**kwargs) -> dict:
    defaults = {
        "id": "abc123",
        "title": "Software Engineer",
        "employer": "Acme Corp",
        "location": "Sydney, NSW",
        "description_snippet": "Great Python role.",
        "source_name": "Adzuna",
        "source_url": "https://adzuna.com/job/123",
        "official_url": "https://adzuna.com/job/123",
    }
    defaults.update(kwargs)
    return defaults


class TestNormalizeJob:
    def test_returns_job_listing(self):
        result = normalize_job(make_raw())
        assert isinstance(result, JobListing)

    def test_missing_employer_defaults(self):
        result = normalize_job(make_raw(employer=None))
        assert result.employer == "Unknown Employer"

    def test_missing_location_defaults(self):
        result = normalize_job(make_raw(location=None))
        assert result.location == "Australia"

    def test_missing_title_defaults(self):
        result = normalize_job(make_raw(title=None))
        assert result.title == "Untitled Role"

    def test_description_truncated(self):
        long_desc = "x" * 1000
        result = normalize_job(make_raw(description_snippet=long_desc))
        assert len(result.description_snippet) <= 803

    def test_salary_zero_becomes_none(self):
        result = normalize_job(make_raw(salary="0"))
        assert result.salary is None

    def test_official_url_fallback_to_source_url(self):
        result = normalize_job(make_raw(official_url=None))
        assert result.official_url == make_raw()["source_url"]

    def test_none_work_type_preserved(self):
        result = normalize_job(make_raw(work_type=None))
        assert result.work_type is None

    def test_extra_fields_ignored(self):
        raw = make_raw(random_field="ignored_value")
        result = normalize_job(raw)
        assert isinstance(result, JobListing)

    def test_stable_id_generated_when_missing(self):
        raw = make_raw()
        del raw["id"]
        result = normalize_job(raw)
        assert result.id is not None and len(result.id) > 0

    def test_description_from_description_key(self):
        raw = make_raw()
        del raw["description_snippet"]
        raw["description"] = "Python developer role"
        result = normalize_job(raw)
        assert "Python" in result.description_snippet


class TestDeduplicateJobs:
    def _make_job(self, id, title, employer, url="", official_url=None) -> JobListing:
        return JobListing(
            id=id,
            title=title,
            employer=employer,
            location="Sydney",
            source_name="Test",
            source_url=url or f"https://example.com/{id}",
            official_url=official_url,
            description_snippet="",
        )

    def test_no_duplicates_unchanged(self):
        jobs = [
            self._make_job("1", "Software Engineer", "Acme Corp"),
            self._make_job("2", "Data Scientist", "Beta Inc"),
            self._make_job("3", "Product Manager", "Gamma Ltd"),
        ]
        result = deduplicate_jobs(jobs)
        assert len(result) == 3

    def test_identical_jobs_deduped(self):
        jobs = [
            self._make_job("1", "Software Engineer", "Acme Corp"),
            self._make_job("2", "Software Engineer", "Acme Corp"),
        ]
        result = deduplicate_jobs(jobs)
        assert len(result) == 1

    def test_prefers_official_url(self):
        job_without = self._make_job("1", "Software Engineer", "Acme Corp", official_url=None)
        job_with = self._make_job("2", "Software Engineer", "Acme Corp", official_url="https://acme.com/jobs/1")
        result = deduplicate_jobs([job_without, job_with])
        assert len(result) == 1
        assert result[0].official_url == "https://acme.com/jobs/1"

    def test_different_titles_not_deduped(self):
        jobs = [
            self._make_job("1", "Software Engineer", "Acme Corp"),
            self._make_job("2", "DevOps Engineer", "Acme Corp"),
        ]
        result = deduplicate_jobs(jobs)
        assert len(result) == 2

    def test_slightly_different_employers_deduped(self):
        # Very similar titles and employers should be deduped
        jobs = [
            self._make_job("1", "Senior Software Engineer", "Acme Corporation"),
            self._make_job("2", "Senior Software Engineer", "Acme Corporation"),
        ]
        result = deduplicate_jobs(jobs)
        assert len(result) == 1

    def test_empty_input(self):
        result = deduplicate_jobs([])
        assert result == []

    def test_single_job(self):
        jobs = [self._make_job("1", "Software Engineer", "Acme")]
        result = deduplicate_jobs(jobs)
        assert len(result) == 1
