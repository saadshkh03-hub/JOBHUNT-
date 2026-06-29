from __future__ import annotations
from .models import CandidateProfile, SearchRequest

# Map of role family -> adjacent/similar titles to try
ADJACENT_TITLES = {
    "Software Engineer": [
        "Developer", "Software Developer", "Full Stack Developer",
        "Backend Developer", "Frontend Developer", "DevOps Engineer",
        "Platform Engineer", "Site Reliability Engineer",
    ],
    "Data Analyst": [
        "Business Intelligence Analyst", "Reporting Analyst",
        "Business Analyst", "Insights Analyst", "Data Specialist",
    ],
    "Data Scientist": [
        "Machine Learning Engineer", "AI Engineer", "Data Analyst",
        "Research Scientist", "Quantitative Analyst",
    ],
    "Data Engineer": [
        "ETL Developer", "Platform Engineer", "Analytics Engineer",
        "Data Architect", "Database Developer",
    ],
    "Cloud / DevOps Engineer": [
        "Infrastructure Engineer", "Platform Engineer", "Site Reliability Engineer",
        "Systems Engineer", "Cloud Architect",
    ],
    "Cybersecurity Analyst": [
        "Security Engineer", "Information Security Officer",
        "Security Consultant", "SOC Analyst", "GRC Analyst",
    ],
    "Project Manager": [
        "Programme Manager", "Delivery Manager", "IT Project Manager",
        "Change Manager", "Scrum Master", "Product Owner",
    ],
    "Business Analyst": [
        "Systems Analyst", "Process Analyst", "Functional Consultant",
        "Product Analyst", "Transformation Analyst",
    ],
    "Financial Analyst": [
        "Finance Business Partner", "Commercial Analyst", "FP&A Analyst",
        "Investment Analyst", "Corporate Finance Analyst",
    ],
    "Accountant": [
        "Management Accountant", "Financial Accountant", "CPA",
        "Tax Accountant", "Finance Officer",
    ],
    "HR Professional": [
        "People and Culture Advisor", "HR Business Partner",
        "Talent Acquisition Specialist", "Organisational Development Advisor",
    ],
    "Marketing Professional": [
        "Digital Marketing Specialist", "Content Marketing Manager",
        "Brand Manager", "Marketing Coordinator", "Growth Manager",
    ],
    "UX/UI Designer": [
        "Product Designer", "Interaction Designer", "UX Researcher",
        "Digital Designer", "Service Designer",
    ],
    "Policy Officer": [
        "Policy Analyst", "Policy Advisor", "Senior Policy Officer",
        "Research Officer", "Regulatory Affairs Officer",
    ],
    "Communications Officer": [
        "Media Officer", "Public Affairs Officer", "Content Officer",
        "Stakeholder Engagement Officer", "Social Media Manager",
    ],
}

# Radius expansion steps
RADIUS_EXPANSION = [50, 100, 250]


def generate_similar_queries(
    candidate: CandidateProfile,
    search_request: SearchRequest,
) -> list[dict]:
    """
    Generate alternative search queries to expand results when there are
    too few strong matches. Returns list of dicts with 'query', 'location',
    'radius_km' keys to try.
    """
    queries = []

    # 1. Adjacent titles from role families
    for family in candidate.role_families[:3]:
        adjacent = ADJACENT_TITLES.get(family, [])
        for title in adjacent[:3]:
            if title.lower() != search_request.job_title.lower():
                queries.append({
                    "query": title,
                    "location": search_request.location,
                    "radius_km": search_request.radius_km,
                })

    # 2. Skills-based queries
    priority_skills = candidate.skills[:5]
    for skill in priority_skills:
        if len(skill) > 3:
            queries.append({
                "query": skill,
                "location": search_request.location,
                "radius_km": search_request.radius_km,
            })

    # 3. Wider radius with original query
    if search_request.job_title:
        for radius in RADIUS_EXPANSION:
            if radius > search_request.radius_km:
                queries.append({
                    "query": search_request.job_title,
                    "location": search_request.location,
                    "radius_km": radius,
                })
                break  # Only one radius expansion per call

    # 4. Role family as direct search
    for family in candidate.role_families[:2]:
        queries.append({
            "query": family,
            "location": search_request.location,
            "radius_km": search_request.radius_km,
        })

    # Deduplicate
    seen = set()
    unique = []
    for q in queries:
        key = (q["query"].lower(), q["location"].lower(), q["radius_km"])
        if key not in seen:
            seen.add(key)
            unique.append(q)

    return unique[:10]  # Limit expansion queries
