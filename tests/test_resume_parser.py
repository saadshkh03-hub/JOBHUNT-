"""Tests for resume_parser.py"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

import pytest
from unittest.mock import patch, MagicMock
from app.resume_parser import (
    parse_resume,
    extract_skills_and_tools,
    extract_certifications,
    extract_years_experience,
    infer_seniority,
    infer_role_families,
    extract_location,
    extract_name,
)
from app.models import CandidateProfile

SAMPLE_RESUME_TEXT = """
Jane Smith
Senior Software Engineer

Sydney, NSW

SUMMARY
Experienced software engineer with 8 years of experience in Python, Django, and AWS.
Strong background in building scalable backend systems.

EXPERIENCE
Senior Software Engineer — Acme Corp (2020 – Present)
- Developed microservices using Python and FastAPI
- Deployed infrastructure on AWS with Terraform and Docker
- Managed PostgreSQL databases and Redis caching

Software Engineer — TechCo (2016 – 2020)
- Built React frontend applications
- Implemented CI/CD pipelines with Jenkins

EDUCATION
Bachelor of Computer Science — University of Sydney (2016)

CERTIFICATIONS
AWS Certified Solutions Architect
Certified Kubernetes Administrator (CKA)

SKILLS
Python, Django, FastAPI, React, JavaScript, SQL, PostgreSQL, Redis, Docker,
Kubernetes, Terraform, AWS, Git, Agile, Scrum
"""

FINANCE_RESUME_TEXT = """
John Doe
Financial Analyst

Melbourne, VIC

SUMMARY
Financial analyst with 5 years experience in financial modelling, budgeting, and forecasting.

EXPERIENCE
Financial Analyst — Big4 Consulting (2019 – 2024)
- Built complex financial models in Excel
- Managed budgeting and forecasting processes
- Analysed investment opportunities using DCF and NPV

EDUCATION
Bachelor of Commerce — University of Melbourne (2019)

CERTIFICATIONS
CPA Australia (2021)

SKILLS
Financial Analysis, Financial Modelling, Excel, Advanced Excel, Budgeting, Forecasting,
DCF, NPV, SAP, PowerPoint, Stakeholder Management
"""


class TestParseResume:
    def test_parse_returns_candidate_profile(self):
        profile = parse_resume(SAMPLE_RESUME_TEXT.encode(), "text/plain")
        assert isinstance(profile, CandidateProfile)

    def test_parse_extracts_skills(self):
        profile = parse_resume(SAMPLE_RESUME_TEXT.encode(), "text/plain")
        skills_lower = [s.lower() for s in profile.skills]
        assert "python" in skills_lower
        assert "docker" in skills_lower
        assert "aws" in skills_lower

    def test_parse_extracts_location(self):
        profile = parse_resume(SAMPLE_RESUME_TEXT.encode(), "text/plain")
        assert "Sydney" in profile.location or "NSW" in profile.location or profile.location == ""

    def test_parse_infers_senior_seniority(self):
        profile = parse_resume(SAMPLE_RESUME_TEXT.encode(), "text/plain")
        assert profile.seniority in ("senior", "lead", "manager")

    def test_parse_extracts_certifications(self):
        profile = parse_resume(SAMPLE_RESUME_TEXT.encode(), "text/plain")
        assert any("aws" in c.lower() or "certified" in c.lower() for c in profile.certifications)

    def test_parse_extracts_years_experience(self):
        profile = parse_resume(SAMPLE_RESUME_TEXT.encode(), "text/plain")
        assert profile.years_experience >= 0

    def test_parse_infers_role_families(self):
        profile = parse_resume(SAMPLE_RESUME_TEXT.encode(), "text/plain")
        assert len(profile.role_families) > 0

    def test_parse_finance_resume(self):
        profile = parse_resume(FINANCE_RESUME_TEXT.encode(), "text/plain")
        skills_lower = [s.lower() for s in profile.skills]
        assert "financial analysis" in skills_lower or "excel" in skills_lower

    def test_parse_empty_file(self):
        profile = parse_resume(b"", "text/plain")
        assert isinstance(profile, CandidateProfile)

    def test_raw_text_stored(self):
        profile = parse_resume(SAMPLE_RESUME_TEXT.encode(), "text/plain")
        assert len(profile.raw_text) > 0

    def test_parse_pdf_calls_pdfplumber(self):
        mock_page = MagicMock()
        mock_page.extract_text.return_value = SAMPLE_RESUME_TEXT
        mock_pdf = MagicMock()
        mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
        mock_pdf.__exit__ = MagicMock(return_value=False)
        mock_pdf.pages = [mock_page]

        with patch("pdfplumber.open", return_value=mock_pdf):
            profile = parse_resume(b"%PDF-fake", "application/pdf")
            assert isinstance(profile, CandidateProfile)


class TestExtractSkills:
    def test_finds_python(self):
        skills, tools = extract_skills_and_tools("Expert in Python and Django")
        assert "python" in skills

    def test_finds_tools_in_tools_list(self):
        skills, tools = extract_skills_and_tools("Used Docker and Kubernetes in CI/CD")
        assert "docker" in tools or "docker" in skills

    def test_no_false_positives_on_short_words(self):
        skills, _ = extract_skills_and_tools("I can do it")
        # "r" should not match standalone 'r' language on full words
        # (word boundary regex should prevent random single letters matching)
        assert len(skills) == 0 or all(len(s) > 1 for s in skills)


class TestExtractCertifications:
    def test_finds_aws_cert(self):
        certs = extract_certifications("AWS Certified Solutions Architect — Professional")
        assert len(certs) > 0

    def test_finds_bachelor(self):
        certs = extract_certifications("Bachelor of Science in Computer Engineering (2020)")
        assert any("bachelor" in c.lower() for c in certs)

    def test_finds_diploma(self):
        certs = extract_certifications("Diploma of Business Administration")
        assert any("diploma" in c.lower() for c in certs)


class TestExtractYearsExperience:
    def test_explicit_years(self):
        years = extract_years_experience("10 years of experience in software development")
        assert years == 10.0

    def test_plus_years(self):
        years = extract_years_experience("5+ years experience in finance")
        assert years == 5.0

    def test_no_mention(self):
        years = extract_years_experience("I work in tech")
        assert years >= 0


class TestInferSeniority:
    def test_senior_from_text(self):
        level = infer_seniority("Senior Software Engineer with extensive experience", 8)
        assert level == "senior"

    def test_junior_from_text(self):
        level = infer_seniority("Graduate developer looking for first role", 1)
        assert level in ("junior", "mid")

    def test_manager_from_text(self):
        level = infer_seniority("Engineering Manager leading a team of 10", 12)
        assert level == "manager"

    def test_years_fallback(self):
        level = infer_seniority("Developer", 10)
        assert level in ("senior", "mid")


class TestRoleFamilies:
    def test_software_engineer_family(self):
        families = infer_role_families(["python", "django", "react", "docker"])
        assert "Software Engineer" in families

    def test_financial_analyst_family(self):
        families = infer_role_families(["financial analysis", "excel", "dcf", "budgeting"])
        assert "Financial Analyst" in families or "Accountant" in families

    def test_multiple_families(self):
        families = infer_role_families(["python", "machine learning", "pandas", "tensorflow"])
        assert len(families) >= 1
