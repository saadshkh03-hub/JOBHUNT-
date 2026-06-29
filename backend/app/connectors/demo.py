"""
Demo data connector — provides realistic Australian job listings for local
development and environments where live sources are unavailable.

This connector is ONLY activated when all other connectors return 0 results,
and the UI clearly labels all results as coming from demo data.

Data is carefully crafted to be realistic, role-diverse, and cover major
Australian cities and work types. Never used in production with live sources.
"""
from __future__ import annotations
import hashlib
from typing import Optional
from .base import BaseConnector
from ..models import SourceStatus

_TODAY = "2026-06-29"

DEMO_JOBS = [
    # ── Software / Engineering ────────────────────────────────────────────
    {
        "title": "Senior Python Developer",
        "employer": "Atlassian",
        "location": "Sydney, NSW",
        "work_type": "hybrid",
        "salary": "$140,000 – $170,000 AUD",
        "description": (
            "Join our platform team to build scalable Python microservices. "
            "Requirements: 5+ years Python, Django or FastAPI, PostgreSQL, Redis, Docker, AWS. "
            "Experience with distributed systems and CI/CD pipelines essential. "
            "Preferred: Kubernetes, Terraform, data pipelines. "
            "Full Australian working rights required."
        ),
        "posted_date": "2026-06-27",
        "closing_date": "2026-07-25",
        "tags": ["python", "software", "backend", "engineering"],
    },
    {
        "title": "Full Stack Software Engineer",
        "employer": "Canva",
        "location": "Sydney, NSW",
        "work_type": "hybrid",
        "salary": "$130,000 – $160,000 AUD",
        "description": (
            "Build features used by 150 million users worldwide. "
            "Stack: React, TypeScript, Python, Go, AWS. "
            "You will own end-to-end development of product features. "
            "Requirements: 3+ years full-stack, React, TypeScript, REST APIs. "
            "Must have full Australian working rights."
        ),
        "posted_date": "2026-06-25",
        "closing_date": "2026-07-20",
        "tags": ["software", "fullstack", "react", "typescript", "python"],
    },
    {
        "title": "Backend Software Engineer – Java/Kotlin",
        "employer": "Afterpay",
        "location": "Melbourne, VIC",
        "work_type": "hybrid",
        "salary": "$125,000 – $155,000 AUD",
        "description": (
            "Design and build high-throughput payment processing systems. "
            "Requirements: Java or Kotlin, Spring Boot, microservices, PostgreSQL, Kafka. "
            "Preferred: Kubernetes, AWS, distributed systems. "
            "Must be eligible to work in Australia."
        ),
        "posted_date": "2026-06-24",
        "closing_date": "2026-07-18",
        "tags": ["software", "java", "kotlin", "backend", "engineering"],
    },
    {
        "title": "Platform Engineer (DevOps/SRE)",
        "employer": "REA Group",
        "location": "Melbourne, VIC",
        "work_type": "hybrid",
        "salary": "$135,000 – $160,000 AUD",
        "description": (
            "Build and maintain cloud infrastructure on AWS. "
            "Requirements: Terraform, Kubernetes, Docker, CI/CD, AWS, Linux. "
            "Experience with observability tools (Datadog, Prometheus, Grafana). "
            "Preferred: Python or Go for automation, security hardening. "
            "Australian permanent residency or citizenship required."
        ),
        "posted_date": "2026-06-26",
        "closing_date": "2026-07-22",
        "tags": ["devops", "cloud", "platform", "infrastructure", "engineering"],
    },
    {
        "title": "Cloud Solutions Architect",
        "employer": "Telstra",
        "location": "Sydney, NSW",
        "work_type": "hybrid",
        "salary": "$160,000 – $200,000 AUD",
        "description": (
            "Lead cloud adoption across Telstra's enterprise portfolio. "
            "Requirements: 7+ years IT, 3+ years AWS or Azure architecture, "
            "solution design, stakeholder management. "
            "Preferred: AWS Professional certification, Terraform, Python. "
            "Must be an Australian citizen or permanent resident."
        ),
        "posted_date": "2026-06-22",
        "closing_date": "2026-07-19",
        "tags": ["cloud", "architecture", "aws", "azure", "engineering"],
    },
    {
        "title": "Frontend Developer – React",
        "employer": "Xero",
        "location": "Melbourne, VIC",
        "work_type": "hybrid",
        "salary": "$110,000 – $140,000 AUD",
        "description": (
            "Build beautiful, accessible web experiences for small business owners. "
            "Requirements: React, TypeScript, CSS, testing (Jest/Cypress), REST APIs. "
            "Preferred: GraphQL, design systems, accessibility (WCAG). "
            "Full working rights in Australia required."
        ),
        "posted_date": "2026-06-28",
        "closing_date": "2026-07-28",
        "tags": ["frontend", "react", "typescript", "software"],
    },
    {
        "title": "Software Engineer – Mobile (iOS)",
        "employer": "Commonwealth Bank",
        "location": "Sydney, NSW",
        "work_type": "hybrid",
        "salary": "$120,000 – $150,000 AUD",
        "description": (
            "Build the CommBank iOS app used by 8 million Australians. "
            "Requirements: Swift, Xcode, UIKit/SwiftUI, REST APIs, Agile. "
            "Preferred: accessibility, banking or fintech experience. "
            "Australian citizenship or permanent residency required."
        ),
        "posted_date": "2026-06-20",
        "closing_date": "2026-07-15",
        "tags": ["mobile", "ios", "swift", "software"],
    },
    {
        "title": "Junior Software Developer",
        "employer": "Atlassian",
        "location": "Sydney, NSW",
        "work_type": "onsite",
        "salary": "$80,000 – $100,000 AUD",
        "description": (
            "Great entry-level role for graduates or developers with 1-2 years experience. "
            "Requirements: Python or JavaScript, basic SQL, version control (Git). "
            "Preferred: university CS degree, internship experience. "
            "Must have full working rights in Australia."
        ),
        "posted_date": "2026-06-28",
        "closing_date": "2026-07-30",
        "tags": ["software", "junior", "python", "javascript"],
    },
    # ── Data / Analytics ──────────────────────────────────────────────────
    {
        "title": "Senior Data Engineer",
        "employer": "Woolworths Group",
        "location": "Sydney, NSW",
        "work_type": "hybrid",
        "salary": "$135,000 – $165,000 AUD",
        "description": (
            "Build and maintain large-scale data pipelines for Australia's biggest retailer. "
            "Requirements: Python, Spark, Airflow, dbt, SQL, cloud data warehouse (BigQuery/Snowflake). "
            "Preferred: Kafka, data modelling, AWS or GCP. "
            "Must have full Australian working rights."
        ),
        "posted_date": "2026-06-26",
        "closing_date": "2026-07-23",
        "tags": ["data", "python", "engineering", "pipeline"],
    },
    {
        "title": "Data Scientist – NLP/ML",
        "employer": "NAB",
        "location": "Melbourne, VIC",
        "work_type": "hybrid",
        "salary": "$130,000 – $160,000 AUD",
        "description": (
            "Apply machine learning to real-world banking challenges. "
            "Requirements: Python, scikit-learn, TensorFlow or PyTorch, SQL, statistics. "
            "Preferred: NLP, transformer models, MLOps, Databricks. "
            "Must be eligible to work in Australia."
        ),
        "posted_date": "2026-06-25",
        "closing_date": "2026-07-20",
        "tags": ["data science", "ml", "python", "ai", "analytics"],
    },
    {
        "title": "Business Intelligence Analyst",
        "employer": "Medibank",
        "location": "Melbourne, VIC",
        "work_type": "hybrid",
        "salary": "$95,000 – $115,000 AUD",
        "description": (
            "Deliver insights and dashboards to drive business decisions. "
            "Requirements: SQL, Power BI or Tableau, Excel, data visualisation. "
            "Preferred: Python, Snowflake, stakeholder management. "
            "Full working rights in Australia required."
        ),
        "posted_date": "2026-06-27",
        "closing_date": "2026-07-24",
        "tags": ["analytics", "bi", "sql", "data"],
    },
    {
        "title": "Data Analyst – Marketing",
        "employer": "Seek",
        "location": "Melbourne, VIC",
        "work_type": "hybrid",
        "salary": "$85,000 – $110,000 AUD",
        "description": (
            "Analyse marketing performance and customer behaviour data. "
            "Requirements: SQL, Excel, Google Analytics, A/B testing, data storytelling. "
            "Preferred: Python, Tableau, customer journey analysis. "
            "Full working rights in Australia."
        ),
        "posted_date": "2026-06-24",
        "closing_date": "2026-07-21",
        "tags": ["analytics", "data", "sql", "marketing"],
    },
    # ── Cybersecurity ─────────────────────────────────────────────────────
    {
        "title": "Cybersecurity Analyst",
        "employer": "Department of Home Affairs",
        "location": "Canberra, ACT",
        "work_type": "onsite",
        "salary": "$92,000 – $112,000 AUD",
        "description": (
            "Protect critical government systems from cyber threats. "
            "Requirements: Security incident response, SIEM tools, network security, "
            "vulnerability assessment, ASD Essential Eight. "
            "Preferred: CISSP or CISM certification, Python scripting. "
            "MUST be an Australian citizen. Baseline security clearance required."
        ),
        "posted_date": "2026-06-23",
        "closing_date": "2026-07-14",
        "eligibility_notes": "Australian citizenship required. Baseline clearance required.",
        "tags": ["security", "cyber", "government", "aps"],
    },
    {
        "title": "Senior Security Engineer",
        "employer": "Macquarie Group",
        "location": "Sydney, NSW",
        "work_type": "hybrid",
        "salary": "$145,000 – $175,000 AUD",
        "description": (
            "Lead security engineering across Macquarie's global infrastructure. "
            "Requirements: Cloud security (AWS/Azure), penetration testing, "
            "identity management, Python or Go, SIEM, CISSP or equivalent. "
            "Preferred: DevSecOps, container security, financial services experience. "
            "Australian permanent residency or citizenship."
        ),
        "posted_date": "2026-06-22",
        "closing_date": "2026-07-16",
        "tags": ["security", "cloud", "engineering"],
    },
    {
        "title": "Information Security Officer",
        "employer": "NSW Health",
        "location": "Sydney, NSW",
        "work_type": "hybrid",
        "salary": "$115,000 – $135,000 AUD",
        "description": (
            "Manage information security governance and compliance across NSW Health. "
            "Requirements: ISO 27001, risk management, policy development, "
            "stakeholder engagement, PSPF familiarity. "
            "Preferred: health sector experience, CISM, project management. "
            "Australian citizen or permanent resident."
        ),
        "posted_date": "2026-06-21",
        "closing_date": "2026-07-17",
        "tags": ["security", "government", "risk", "compliance"],
    },
    # ── Project / Programme Management ────────────────────────────────────
    {
        "title": "Senior IT Project Manager",
        "employer": "ANZ Bank",
        "location": "Melbourne, VIC",
        "work_type": "hybrid",
        "salary": "$130,000 – $160,000 AUD",
        "description": (
            "Lead complex technology transformation programmes. "
            "Requirements: PMP or PRINCE2, 7+ years IT project management, "
            "Agile/Scrum, stakeholder management, risk management, MS Project. "
            "Preferred: banking or financial services, change management. "
            "Full working rights in Australia required."
        ),
        "posted_date": "2026-06-25",
        "closing_date": "2026-07-20",
        "tags": ["project management", "it", "agile", "banking"],
    },
    {
        "title": "Agile Delivery Manager",
        "employer": "Service NSW",
        "location": "Sydney, NSW",
        "work_type": "hybrid",
        "salary": "$118,000 – $138,000 AUD",
        "description": (
            "Lead cross-functional agile teams delivering digital government services. "
            "Requirements: Agile/Scrum, servant leadership, roadmap planning, "
            "stakeholder engagement, delivery risk management. "
            "Preferred: SAFe certification, public sector experience. "
            "Australian citizen or permanent resident preferred."
        ),
        "posted_date": "2026-06-26",
        "closing_date": "2026-07-22",
        "tags": ["agile", "delivery", "project management", "government"],
    },
    {
        "title": "Technology Programme Manager",
        "employer": "Westpac",
        "location": "Sydney, NSW",
        "work_type": "hybrid",
        "salary": "$150,000 – $185,000 AUD",
        "description": (
            "Own delivery of major technology transformation programmes. "
            "Requirements: 10+ years programme management, large-scale IT transformation, "
            "executive stakeholder management, budget management ($10M+). "
            "Preferred: banking, MSP certification. "
            "Full working rights in Australia."
        ),
        "posted_date": "2026-06-20",
        "closing_date": "2026-07-18",
        "tags": ["programme management", "technology", "transformation", "banking"],
    },
    # ── Business Analysis ─────────────────────────────────────────────────
    {
        "title": "Senior Business Analyst",
        "employer": "IAG Insurance",
        "location": "Sydney, NSW",
        "work_type": "hybrid",
        "salary": "$110,000 – $135,000 AUD",
        "description": (
            "Bridge business and technology to deliver effective solutions. "
            "Requirements: Business requirements gathering, process mapping (BPMN), "
            "stakeholder workshops, UAT coordination, JIRA, Agile. "
            "Preferred: insurance or financial services, SQL, Confluence. "
            "Full working rights in Australia required."
        ),
        "posted_date": "2026-06-27",
        "closing_date": "2026-07-25",
        "tags": ["business analysis", "agile", "requirements", "finance"],
    },
    {
        "title": "APS5 Policy Analyst",
        "employer": "Department of Finance",
        "location": "Canberra, ACT",
        "work_type": "onsite",
        "salary": "$83,000 – $92,000 AUD",
        "description": (
            "Contribute to the development of Commonwealth financial management policy. "
            "Requirements: Policy analysis, research, written communication, "
            "stakeholder engagement, government budget process familiarity. "
            "Preferred: economics, public administration, or finance background. "
            "MUST be an Australian citizen. Baseline security clearance required."
        ),
        "posted_date": "2026-06-24",
        "closing_date": "2026-07-10",
        "eligibility_notes": "Australian citizenship required. Baseline clearance required.",
        "tags": ["policy", "government", "aps", "analysis"],
    },
    # ── Finance / Accounting ──────────────────────────────────────────────
    {
        "title": "Senior Financial Analyst",
        "employer": "BHP",
        "location": "Melbourne, VIC",
        "work_type": "hybrid",
        "salary": "$120,000 – $145,000 AUD",
        "description": (
            "Support strategic financial planning and analysis for BHP's operations. "
            "Requirements: CA/CPA qualified, financial modelling (Excel/Python), "
            "FP&A, management reporting, variance analysis. "
            "Preferred: mining, commodities, SAP. "
            "Must have full working rights in Australia."
        ),
        "posted_date": "2026-06-26",
        "closing_date": "2026-07-21",
        "tags": ["finance", "financial analysis", "accounting", "modelling"],
    },
    {
        "title": "Management Accountant",
        "employer": "Coles Group",
        "location": "Melbourne, VIC",
        "work_type": "hybrid",
        "salary": "$95,000 – $115,000 AUD",
        "description": (
            "Deliver accurate management accounts and support business unit leaders. "
            "Requirements: CA/CPA, month-end close, P&L analysis, budgeting, forecasting, "
            "Excel, SAP or Oracle. "
            "Preferred: retail experience, data analytics. "
            "Full working rights in Australia."
        ),
        "posted_date": "2026-06-25",
        "closing_date": "2026-07-19",
        "tags": ["accounting", "finance", "management accounting"],
    },
    # ── Human Resources ───────────────────────────────────────────────────
    {
        "title": "HR Business Partner",
        "employer": "Qantas",
        "location": "Sydney, NSW",
        "work_type": "hybrid",
        "salary": "$110,000 – $130,000 AUD",
        "description": (
            "Partner with business leaders to deliver people and culture outcomes. "
            "Requirements: HR Business partnering, ER/IR, coaching, workforce planning, "
            "change management, Australian employment law. "
            "Preferred: aviation or operations-heavy environment. "
            "Full working rights in Australia."
        ),
        "posted_date": "2026-06-23",
        "closing_date": "2026-07-16",
        "tags": ["hr", "people", "human resources", "business partner"],
    },
    {
        "title": "Talent Acquisition Specialist",
        "employer": "Afterpay",
        "location": "Melbourne, VIC",
        "work_type": "hybrid",
        "salary": "$90,000 – $110,000 AUD",
        "description": (
            "Source and recruit top technology talent for Australia's leading fintech. "
            "Requirements: Technical recruiting, ATS (Greenhouse or Lever), "
            "Boolean search, candidate experience, offer management. "
            "Preferred: fintech or tech startup experience. "
            "Full working rights in Australia."
        ),
        "posted_date": "2026-06-28",
        "closing_date": "2026-07-26",
        "tags": ["hr", "recruitment", "talent acquisition"],
    },
    # ── Marketing / Communications ─────────────────────────────────────────
    {
        "title": "Digital Marketing Manager",
        "employer": "Realestate.com.au",
        "location": "Melbourne, VIC",
        "work_type": "hybrid",
        "salary": "$110,000 – $135,000 AUD",
        "description": (
            "Lead digital marketing campaigns across paid search, SEO, and social. "
            "Requirements: Google Ads, Meta Ads, SEO/SEM, Google Analytics, "
            "A/B testing, campaign management. "
            "Preferred: marketing automation, Salesforce, team leadership. "
            "Full working rights in Australia."
        ),
        "posted_date": "2026-06-27",
        "closing_date": "2026-07-24",
        "tags": ["marketing", "digital", "advertising"],
    },
    {
        "title": "Content and Communications Officer",
        "employer": "City of Melbourne",
        "location": "Melbourne, VIC",
        "work_type": "hybrid",
        "salary": "$85,000 – $100,000 AUD",
        "description": (
            "Create compelling content for council communications channels. "
            "Requirements: copywriting, digital content, social media, "
            "government communications, stakeholder engagement. "
            "Preferred: journalism background, CMS platforms. "
            "Australian citizen or permanent resident preferred."
        ),
        "posted_date": "2026-06-24",
        "closing_date": "2026-07-18",
        "tags": ["communications", "content", "government", "council"],
    },
    # ── UX/Design ─────────────────────────────────────────────────────────
    {
        "title": "Senior UX Designer",
        "employer": "ANZ Bank",
        "location": "Melbourne, VIC",
        "work_type": "hybrid",
        "salary": "$120,000 – $145,000 AUD",
        "description": (
            "Design intuitive digital banking experiences for millions of Australians. "
            "Requirements: User research, interaction design, Figma, prototyping, "
            "usability testing, design systems. "
            "Preferred: accessibility (WCAG), banking or fintech, mentoring. "
            "Full working rights in Australia."
        ),
        "posted_date": "2026-06-26",
        "closing_date": "2026-07-22",
        "tags": ["ux", "design", "figma", "research"],
    },
    # ── Remote / Flexible ─────────────────────────────────────────────────
    {
        "title": "Remote Python Developer",
        "employer": "Culture Amp",
        "location": "Australia (Remote)",
        "work_type": "remote",
        "salary": "$120,000 – $150,000 AUD",
        "description": (
            "Build people analytics features for our HR platform. Fully remote role. "
            "Requirements: Python, Django, PostgreSQL, REST APIs, Git, Agile. "
            "Preferred: React, data pipelines, HR tech. "
            "Must be based in Australia with full working rights."
        ),
        "posted_date": "2026-06-28",
        "closing_date": "2026-07-30",
        "tags": ["python", "software", "remote", "backend"],
    },
    {
        "title": "Remote Data Engineer",
        "employer": "SafetyCulture",
        "location": "Australia (Remote)",
        "work_type": "remote",
        "salary": "$130,000 – $155,000 AUD",
        "description": (
            "Build the data infrastructure powering our global platform. Fully remote. "
            "Requirements: Python, dbt, Airflow, Snowflake, SQL, cloud data platforms. "
            "Preferred: Spark, Kafka, Terraform. "
            "Must be based in Australia with full working rights."
        ),
        "posted_date": "2026-06-27",
        "closing_date": "2026-07-25",
        "tags": ["data", "python", "remote", "engineering"],
    },
    # ── Government / APS ──────────────────────────────────────────────────
    {
        "title": "APS6 ICT Project Manager",
        "employer": "Services Australia",
        "location": "Canberra, ACT",
        "work_type": "hybrid",
        "salary": "$96,000 – $108,000 AUD",
        "description": (
            "Manage ICT projects delivering services to millions of Australians. "
            "Requirements: Project management, Agile, stakeholder engagement, "
            "risk management, ICT delivery experience. "
            "Preferred: PRINCE2 or PMP, government experience. "
            "MUST be an Australian citizen. Baseline security clearance required or obtainable."
        ),
        "posted_date": "2026-06-25",
        "closing_date": "2026-07-11",
        "eligibility_notes": "Australian citizenship required. Baseline clearance required.",
        "tags": ["project management", "government", "aps", "ict"],
    },
    {
        "title": "APS5 Data Analyst",
        "employer": "Australian Bureau of Statistics",
        "location": "Canberra, ACT",
        "work_type": "hybrid",
        "salary": "$83,000 – $92,000 AUD",
        "description": (
            "Analyse and present national statistical data for government reporting. "
            "Requirements: Python or R, SQL, statistical analysis, data visualisation, "
            "report writing. "
            "Preferred: SAS, Tableau, economics or statistics background. "
            "MUST be an Australian citizen. Baseline security clearance required."
        ),
        "posted_date": "2026-06-23",
        "closing_date": "2026-07-09",
        "eligibility_notes": "Australian citizenship required. Baseline clearance required.",
        "tags": ["data", "analytics", "government", "aps", "python"],
    },
    {
        "title": "EL1 Assistant Director – Technology Policy",
        "employer": "Department of Industry",
        "location": "Canberra, ACT",
        "work_type": "hybrid",
        "salary": "$115,000 – $133,000 AUD",
        "description": (
            "Lead technology and digital policy development for Australian industry. "
            "Requirements: Policy development, strategic thinking, executive writing, "
            "stakeholder management, IT or digital industry knowledge. "
            "Preferred: data/AI policy, procurement policy, economics. "
            "MUST be an Australian citizen. NV1 clearance preferred."
        ),
        "posted_date": "2026-06-22",
        "closing_date": "2026-07-08",
        "eligibility_notes": "Australian citizenship required. NV1 security clearance preferred.",
        "tags": ["policy", "government", "aps", "technology"],
    },
    # ── Brisbane ──────────────────────────────────────────────────────────
    {
        "title": "Software Engineer – Python/Go",
        "employer": "Suncorp",
        "location": "Brisbane, QLD",
        "work_type": "hybrid",
        "salary": "$120,000 – $145,000 AUD",
        "description": (
            "Build next-generation insurance platforms at Suncorp. "
            "Requirements: Python or Go, microservices, REST APIs, PostgreSQL, AWS, Docker. "
            "Preferred: Kubernetes, event-driven architecture, insurance domain. "
            "Full working rights in Australia."
        ),
        "posted_date": "2026-06-26",
        "closing_date": "2026-07-22",
        "tags": ["python", "go", "software", "backend", "engineering"],
    },
    {
        "title": "Business Analyst – Digital Transformation",
        "employer": "Queensland Health",
        "location": "Brisbane, QLD",
        "work_type": "hybrid",
        "salary": "$100,000 – $120,000 AUD",
        "description": (
            "Support digital transformation of Queensland's health system. "
            "Requirements: Business analysis, process redesign, requirements gathering, "
            "stakeholder engagement, healthcare systems knowledge. "
            "Preferred: Epic or clinical system experience, BABOK. "
            "Australian citizen or permanent resident required."
        ),
        "posted_date": "2026-06-25",
        "closing_date": "2026-07-19",
        "tags": ["business analysis", "health", "government", "transformation"],
    },
    # ── Perth ─────────────────────────────────────────────────────────────
    {
        "title": "Senior Data Engineer – Mining Analytics",
        "employer": "Rio Tinto",
        "location": "Perth, WA",
        "work_type": "hybrid",
        "salary": "$140,000 – $170,000 AUD",
        "description": (
            "Build data engineering solutions for autonomous mining operations. "
            "Requirements: Python, Spark, Databricks, SQL, cloud (Azure preferred), "
            "data modelling, ETL pipelines. "
            "Preferred: IoT data, time-series analysis, mining industry. "
            "Australian permanent residency or citizenship."
        ),
        "posted_date": "2026-06-24",
        "closing_date": "2026-07-18",
        "tags": ["data", "python", "engineering", "mining", "analytics"],
    },
    # ── Adelaide ──────────────────────────────────────────────────────────
    {
        "title": "Cybersecurity Consultant",
        "employer": "BAE Systems Australia",
        "location": "Adelaide, SA",
        "work_type": "onsite",
        "salary": "$110,000 – $140,000 AUD",
        "description": (
            "Deliver cybersecurity services to Australia's defence sector. "
            "Requirements: Security architecture, penetration testing or GRC, "
            "NIST/ISM frameworks, stakeholder communication. "
            "Preferred: CISSP or CISM, defence sector experience. "
            "MUST be an Australian citizen. NV1 or NV2 security clearance highly desirable."
        ),
        "posted_date": "2026-06-23",
        "closing_date": "2026-07-15",
        "eligibility_notes": "Australian citizenship required. NV1/NV2 clearance highly desirable.",
        "tags": ["security", "defence", "consulting", "government"],
    },
    # ── Council ───────────────────────────────────────────────────────────
    {
        "title": "ICT Business Analyst",
        "employer": "City of Brisbane City Council",
        "location": "Brisbane, QLD",
        "work_type": "hybrid",
        "salary": "$90,000 – $108,000 AUD",
        "description": (
            "Deliver ICT projects and system improvements for Brisbane City Council. "
            "Requirements: Business analysis, ICT systems, requirements documentation, "
            "stakeholder engagement, testing coordination. "
            "Preferred: local government experience, JIRA, Agile. "
            "Australian citizen or permanent resident preferred."
        ),
        "posted_date": "2026-06-27",
        "closing_date": "2026-07-20",
        "tags": ["business analysis", "ict", "council", "government"],
    },
    {
        "title": "GIS Analyst – Urban Planning",
        "employer": "City of Sydney Council",
        "location": "Sydney, NSW",
        "work_type": "hybrid",
        "salary": "$88,000 – $105,000 AUD",
        "description": (
            "Provide GIS analysis and spatial data services for Sydney's planning team. "
            "Requirements: ArcGIS, QGIS, spatial data analysis, SQL, urban planning knowledge. "
            "Preferred: Python (arcpy), data visualisation, council experience. "
            "Australian citizen or permanent resident."
        ),
        "posted_date": "2026-06-22",
        "closing_date": "2026-07-14",
        "tags": ["gis", "analytics", "council", "government", "data"],
    },
    # ── Product Management ────────────────────────────────────────────────
    {
        "title": "Senior Product Manager – Platform",
        "employer": "Atlassian",
        "location": "Sydney, NSW",
        "work_type": "hybrid",
        "salary": "$155,000 – $190,000 AUD",
        "description": (
            "Own the product roadmap for Atlassian's developer platform products. "
            "Requirements: Product management, OKRs, roadmap planning, "
            "user research, data-driven decision making, technical background. "
            "Preferred: B2B SaaS, platform products, engineering background. "
            "Full working rights in Australia."
        ),
        "posted_date": "2026-06-25",
        "closing_date": "2026-07-22",
        "tags": ["product management", "saas", "software", "platform"],
    },
    {
        "title": "Product Owner – Digital Banking",
        "employer": "Westpac",
        "location": "Sydney, NSW",
        "work_type": "hybrid",
        "salary": "$120,000 – $145,000 AUD",
        "description": (
            "Own digital banking features from ideation to launch. "
            "Requirements: Product ownership (SAFe or Scrum), backlog management, "
            "user story writing, stakeholder communication, banking products knowledge. "
            "Preferred: Mobile banking, open banking, API products. "
            "Full working rights in Australia."
        ),
        "posted_date": "2026-06-24",
        "closing_date": "2026-07-20",
        "tags": ["product management", "banking", "agile", "digital"],
    },
]


def _make_id(title: str, employer: str) -> str:
    key = f"{title.lower()}{employer.lower()}"
    return "demo_" + hashlib.md5(key.encode()).hexdigest()[:12]


def _build_jobs(query: str, location: str, work_type: str, limit: int,
                source_filter: str = "all") -> list[dict]:
    query_lower = query.lower()
    loc_lower = location.lower() if location else ""

    scored: list[tuple[int, dict]] = []
    for job in DEMO_JOBS:
        # Apply source filter
        tags = [t.lower() for t in job.get("tags", [])]
        if source_filter == "government" and "government" not in tags and "aps" not in tags:
            continue
        if source_filter == "council" and "council" not in tags:
            continue
        # Basic relevance scoring for demo filtering
        score = 0
        title_lower = job["title"].lower()
        desc_lower = job["description"].lower()
        tags = [t.lower() for t in job.get("tags", [])]
        job_loc = job["location"].lower()

        # Title match
        for word in query_lower.split():
            if len(word) > 2:
                if word in title_lower:
                    score += 4
                if any(word in t for t in tags):
                    score += 2
                if word in desc_lower:
                    score += 1

        # Location match
        if loc_lower and loc_lower != "australia":
            if any(part in job_loc for part in loc_lower.split(",")):
                score += 3
            elif job["work_type"] == "remote":
                score += 2
        else:
            score += 1  # Australia-wide search — all are relevant

        # Work type match
        if work_type and work_type != "any":
            if job.get("work_type") == work_type:
                score += 2
            elif job.get("work_type") == "remote":
                score += 1

        if score > 0:
            scored.append((score, job))

    scored.sort(key=lambda x: x[0], reverse=True)

    result = []
    for _, job in scored[:limit]:
        jid = _make_id(job["title"], job["employer"])
        result.append({
            "id": jid,
            "title": job["title"],
            "employer": job["employer"],
            "location": job["location"],
            "work_type": job.get("work_type"),
            "salary": job.get("salary"),
            "description_snippet": job["description"],
            "source_name": "Demo Data",
            "source_url": f"https://example.com/jobs/{jid}",
            "official_url": None,
            "posted_date": job.get("posted_date"),
            "closing_date": job.get("closing_date"),
            "eligibility_notes": job.get("eligibility_notes"),
        })

    return result


class DemoConnector(BaseConnector):
    """
    Fallback connector using realistic sample Australian job data.
    Only activated when all live sources return 0 results.
    Clearly labeled as demo data in source status.
    """
    name = "Demo Data"

    async def search(
        self,
        query: str,
        location: str,
        radius_km: int = 50,
        work_type: str = "any",
        results_per_page: int = 20,
        source_filter: str = "all",
    ) -> tuple[list[dict], SourceStatus]:
        jobs = _build_jobs(query, location, work_type, results_per_page, source_filter)
        return jobs, SourceStatus(
            name=self.name,
            status="available",
            message=(
                "Showing demo data — live job sources are unavailable in this environment. "
                "Configure ADZUNA_APP_ID and ADZUNA_APP_KEY (free at developer.adzuna.com) "
                "to search live Australian job listings."
            ),
        )
