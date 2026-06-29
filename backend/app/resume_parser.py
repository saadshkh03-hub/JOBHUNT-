from __future__ import annotations
import re
import io
from typing import Optional
from .models import CandidateProfile

# ---------------------------------------------------------------------------
# Comprehensive skills dictionary
# ---------------------------------------------------------------------------
SKILLS_DICT = {
    # Programming languages
    "python", "java", "javascript", "typescript", "c#", "c++", "c", "ruby",
    "go", "golang", "rust", "kotlin", "swift", "scala", "r", "matlab",
    "perl", "php", "bash", "shell", "powershell", "vba", "sql", "plsql",
    "dart", "elixir", "haskell", "lua", "groovy",
    # Web / Frontend
    "react", "angular", "vue", "vue.js", "next.js", "nuxt", "svelte",
    "html", "css", "sass", "less", "bootstrap", "tailwind", "jquery",
    "webpack", "vite", "babel", "graphql", "rest", "restful", "api",
    "websocket", "oauth", "openapi", "swagger",
    # Backend frameworks
    "django", "flask", "fastapi", "spring", "spring boot", "express",
    "node.js", "nodejs", "rails", "laravel", "asp.net", ".net", "dotnet",
    "fastify", "nestjs",
    # Data / ML / AI
    "machine learning", "deep learning", "nlp", "natural language processing",
    "computer vision", "tensorflow", "pytorch", "keras", "scikit-learn",
    "pandas", "numpy", "scipy", "matplotlib", "seaborn", "plotly",
    "spark", "pyspark", "hadoop", "hive", "kafka", "airflow",
    "data analysis", "data science", "data engineering", "etl",
    "statistics", "regression", "classification", "clustering",
    "a/b testing", "feature engineering", "model deployment",
    "llm", "openai", "langchain", "hugging face",
    # Cloud / DevOps
    "aws", "azure", "gcp", "google cloud", "cloud", "devops", "ci/cd",
    "docker", "kubernetes", "helm", "terraform", "ansible", "chef",
    "puppet", "jenkins", "github actions", "gitlab ci", "circleci",
    "linux", "unix", "networking", "load balancing", "microservices",
    "serverless", "lambda", "ec2", "s3", "rds", "cloudformation",
    # Databases
    "postgresql", "mysql", "sqlite", "mongodb", "redis", "elasticsearch",
    "cassandra", "dynamodb", "oracle", "sql server", "mssql",
    "neo4j", "influxdb", "bigquery", "snowflake", "redshift",
    # Project management / Soft skills
    "agile", "scrum", "kanban", "waterfall", "prince2", "pmp",
    "jira", "confluence", "trello", "asana", "monday.com",
    "stakeholder management", "requirements gathering", "business analysis",
    "product management", "project management", "change management",
    "risk management", "vendor management", "contract management",
    # Finance / Accounting
    "financial analysis", "financial modelling", "budgeting", "forecasting",
    "accounting", "bookkeeping", "tax", "audit", "compliance",
    "xero", "myob", "sap", "oracle financials", "quickbooks",
    "excel", "advanced excel", "financial reporting", "ifrs", "aasb",
    "treasury", "investments", "valuation", "dcf", "npv",
    # HR / People
    "recruitment", "talent acquisition", "onboarding", "performance management",
    "employee relations", "training", "learning and development", "l&d",
    "workday", "successfactors", "payroll", "hris", "industrial relations",
    # Marketing / Communications
    "digital marketing", "seo", "sem", "google ads", "facebook ads",
    "social media", "content marketing", "copywriting", "brand management",
    "email marketing", "crm", "salesforce", "hubspot", "adobe",
    "public relations", "communications", "media relations",
    # Design
    "figma", "sketch", "adobe xd", "photoshop", "illustrator", "indesign",
    "ux", "ui", "user experience", "user research", "wireframing",
    "prototyping", "accessibility", "wcag",
    # Healthcare
    "clinical", "nursing", "patient care", "electronic health records",
    "ehr", "emr", "medical coding", "healthcare", "aged care",
    "mental health", "occupational therapy", "physiotherapy",
    # Government / Policy
    "policy", "policy development", "legislation", "regulatory",
    "government", "public sector", "cabinet submissions", "briefs",
    "ministerial", "procurement", "grant management", "aps",
    # Legal
    "legal research", "contracts", "litigation", "compliance",
    "intellectual property", "corporate law", "employment law",
    # Security
    "cybersecurity", "information security", "iso 27001", "nist",
    "penetration testing", "soc", "siem", "firewall", "vpn",
    "identity management", "iam", "pci dss",
    # Engineering
    "autocad", "solidworks", "revit", "civil engineering", "structural",
    "mechanical", "electrical", "project delivery", "construction",
    # General tools
    "microsoft office", "word", "powerpoint", "outlook", "teams",
    "sharepoint", "power bi", "tableau", "qlik", "looker",
    "git", "github", "gitlab", "bitbucket",
    "zoom", "slack", "notion",
}

TOOLS_KEYWORDS = {
    "jira", "confluence", "github", "gitlab", "bitbucket", "jenkins",
    "docker", "kubernetes", "terraform", "ansible", "git",
    "excel", "powerpoint", "word", "outlook", "teams", "sharepoint",
    "slack", "zoom", "notion", "trello", "asana", "monday.com",
    "salesforce", "hubspot", "xero", "myob", "sap", "workday",
    "figma", "sketch", "adobe xd", "photoshop", "illustrator",
    "power bi", "tableau", "qlik", "looker", "grafana",
    "aws", "azure", "gcp",
    "pytorch", "tensorflow", "keras",
    "pandas", "numpy", "spark",
    "postman", "insomnia", "datadog", "splunk", "pagerduty",
}

AUSTRALIAN_CITIES = [
    "sydney", "melbourne", "brisbane", "perth", "adelaide", "canberra",
    "hobart", "darwin", "gold coast", "newcastle", "wollongong",
    "geelong", "sunshine coast", "townsville", "cairns", "toowoomba",
    "ballarat", "bendigo", "albury", "wodonga", "launceston",
    "mackay", "rockhampton", "bundaberg", "hervey bay", "wagga wagga",
    "port macquarie", "tamworth", "orange", "dubbo", "lismore",
    "mildura", "shepparton", "alice springs", "mount gambier",
    "NSW", "VIC", "QLD", "WA", "SA", "TAS", "NT", "ACT",
    "new south wales", "victoria", "queensland", "western australia",
    "south australia", "tasmania", "northern territory",
    "australian capital territory",
]

SENIORITY_KEYWORDS = {
    "junior": ["junior", "graduate", "grad", "entry level", "entry-level",
               "associate", "trainee", "intern", "cadet", "apprentice"],
    "mid": ["mid", "intermediate", "mid-level", "analyst", "officer",
            "coordinator", "specialist", "consultant"],
    "senior": ["senior", "sr.", "sr ", "experienced", "expert", "principal",
               "staff", "level iii", "level 3"],
    "lead": ["lead", "team lead", "technical lead", "tech lead", "chapter lead"],
    "manager": ["manager", "head of", "director", "managing", "management"],
    "executive": ["executive", "vp", "vice president", "cto", "ceo", "cfo",
                  "coo", "chief", "general manager", "gm"],
}

ROLE_FAMILY_MAPPINGS = {
    "Software Engineer": [
        "python", "java", "javascript", "typescript", "c#", "c++", "ruby",
        "go", "golang", "rust", "react", "angular", "vue", "django", "flask",
        "fastapi", "spring", "express", "node.js", "nodejs", "software",
        "developer", "engineer", "programming", "coding", "devops",
        "microservices", "api", "backend", "frontend", "full stack",
    ],
    "Data Analyst": [
        "data analysis", "sql", "excel", "power bi", "tableau", "qlik",
        "looker", "reporting", "dashboard", "analytics", "business intelligence",
        "bi", "data visualisation", "pivot", "vlookup",
    ],
    "Data Scientist": [
        "machine learning", "deep learning", "python", "r", "statistics",
        "tensorflow", "pytorch", "scikit-learn", "pandas", "numpy",
        "data science", "predictive modelling", "nlp", "computer vision",
    ],
    "Data Engineer": [
        "etl", "spark", "pyspark", "hadoop", "kafka", "airflow", "pipeline",
        "data warehouse", "snowflake", "bigquery", "redshift", "dbt",
        "data engineering", "databricks",
    ],
    "Cloud / DevOps Engineer": [
        "aws", "azure", "gcp", "docker", "kubernetes", "terraform", "ansible",
        "ci/cd", "jenkins", "github actions", "devops", "sre", "infrastructure",
        "linux", "cloud", "serverless",
    ],
    "Cybersecurity Analyst": [
        "cybersecurity", "information security", "iso 27001", "nist",
        "penetration testing", "soc", "siem", "firewall", "security",
        "iam", "vulnerability", "incident response",
    ],
    "Project Manager": [
        "project management", "agile", "scrum", "prince2", "pmp", "waterfall",
        "stakeholder management", "project delivery", "gantt", "ms project",
        "programme management", "change management",
    ],
    "Business Analyst": [
        "business analysis", "requirements gathering", "user stories",
        "process mapping", "bpmn", "functional specification", "gap analysis",
        "business analyst", "systems analyst",
    ],
    "Financial Analyst": [
        "financial analysis", "financial modelling", "forecasting", "budgeting",
        "dcf", "npv", "valuation", "excel", "ifrs", "aasb", "accounting",
        "treasury", "investments", "financial reporting",
    ],
    "Accountant": [
        "accounting", "bookkeeping", "tax", "audit", "xero", "myob", "sap",
        "accounts payable", "accounts receivable", "reconciliation",
        "financial statements", "cpa", "ca", "cpa australia",
    ],
    "HR Professional": [
        "recruitment", "talent acquisition", "onboarding", "performance management",
        "employee relations", "payroll", "hris", "workday", "training",
        "learning and development", "industrial relations", "hr",
    ],
    "Marketing Professional": [
        "digital marketing", "seo", "sem", "social media", "content marketing",
        "brand management", "email marketing", "crm", "salesforce", "hubspot",
        "marketing", "campaigns", "google ads",
    ],
    "UX/UI Designer": [
        "ux", "ui", "figma", "sketch", "adobe xd", "user experience",
        "user research", "wireframing", "prototyping", "accessibility",
        "design", "interaction design",
    ],
    "Policy Officer": [
        "policy", "policy development", "legislation", "regulatory",
        "government", "public sector", "briefs", "ministerial",
        "cabinet submissions", "aps", "public administration",
    ],
    "Communications Officer": [
        "communications", "public relations", "media relations", "copywriting",
        "editing", "stakeholder communications", "internal communications",
        "writing", "content", "journalism",
    ],
}

INDUSTRY_KEYWORDS = {
    "Technology": ["software", "tech", "it", "digital", "saas", "startup", "ai"],
    "Finance": ["banking", "finance", "investment", "insurance", "superannuation",
                "financial services", "fintech"],
    "Government": ["government", "public sector", "aps", "federal", "state government",
                   "local government", "council", "department", "agency"],
    "Healthcare": ["health", "hospital", "medical", "clinical", "pharmaceutical",
                   "aged care", "nursing"],
    "Education": ["education", "university", "school", "teaching", "training",
                  "vocational", "tafe", "higher education"],
    "Construction": ["construction", "infrastructure", "engineering", "property",
                     "real estate", "building"],
    "Retail": ["retail", "e-commerce", "ecommerce", "consumer", "fmcg"],
    "Mining": ["mining", "resources", "oil and gas", "energy", "utilities"],
    "Consulting": ["consulting", "advisory", "professional services", "management consulting"],
    "Legal": ["law", "legal", "solicitor", "barrister", "litigation", "compliance"],
}


def extract_text_from_pdf(file_bytes: bytes) -> str:
    import fitz  # pymupdf — no cryptography dependency
    text_parts = []
    with fitz.open(stream=file_bytes, filetype="pdf") as doc:
        for page in doc:
            page_text = page.get_text("text")
            if page_text and page_text.strip():
                text_parts.append(page_text)
    return "\n".join(text_parts)


def extract_text_from_docx(file_bytes: bytes) -> str:
    from docx import Document
    doc = Document(io.BytesIO(file_bytes))
    paragraphs = []
    for para in doc.paragraphs:
        if para.text.strip():
            paragraphs.append(para.text)
    # Also extract from tables
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                if cell.text.strip():
                    paragraphs.append(cell.text)
    return "\n".join(paragraphs)


def extract_text(file_bytes: bytes, content_type: str) -> str:
    ct = content_type.lower()
    if "pdf" in ct:
        return extract_text_from_pdf(file_bytes)
    elif "docx" in ct or "openxmlformats" in ct or "msword" in ct:
        return extract_text_from_docx(file_bytes)
    else:
        # Try PDF first, then DOCX, fallback to plain text
        try:
            text = extract_text_from_pdf(file_bytes)
            if text.strip():
                return text
        except Exception:
            pass
        try:
            text = extract_text_from_docx(file_bytes)
            if text.strip():
                return text
        except Exception:
            pass
        return file_bytes.decode("utf-8", errors="replace")


def extract_name(text: str) -> str:
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    # The first non-empty line is often the name (if it's short and title-cased)
    for line in lines[:5]:
        words = line.split()
        if 2 <= len(words) <= 4 and all(
            w[0].isupper() for w in words if len(w) > 1 and w.isalpha()
        ):
            return line
    return ""


def extract_skills_and_tools(text: str) -> tuple[list[str], list[str]]:
    text_lower = text.lower()
    found_skills = []
    found_tools = []
    for skill in SKILLS_DICT:
        # word boundary match
        pattern = r"(?<![a-z0-9])" + re.escape(skill) + r"(?![a-z0-9])"
        if re.search(pattern, text_lower):
            found_skills.append(skill)
            if skill in TOOLS_KEYWORDS:
                found_tools.append(skill)
    return list(set(found_skills)), list(set(found_tools))


def extract_certifications(text: str) -> list[str]:
    patterns = [
        r"(?i)(cert(?:ified|ificate|ification)?[\w\s\-/]*(?:in|of)?[\w\s\-/]{3,40})",
        r"(?i)(diploma[\w\s\-/]{3,40})",
        r"(?i)(bachelor[\w\s\-/]{3,40})",
        r"(?i)(master[\w\s\-/]{3,40})",
        r"(?i)(ph\.?d[\w\s\-/]{0,40})",
        r"(?i)(aws[\s\-]certified[\w\s\-/]{3,40})",
        r"(?i)(cpa\b[\w\s\-/]{0,40})",
        r"(?i)(ca\b[\w\s\-/]{0,30}(?:australia|chartered))",
        r"(?i)(prince2[\w\s\-/]{0,30})",
        r"(?i)(pmp\b[\w\s\-/]{0,30})",
        r"(?i)(cissp\b[\w\s\-/]{0,30})",
        r"(?i)(cism\b[\w\s\-/]{0,30})",
        r"(?i)(itil[\w\s\-/]{0,30})",
        r"(?i)(agile[\s\-]certified[\w\s\-/]{0,30})",
        r"(?i)(scrum[\s\-]master[\w\s\-/]{0,30})",
        r"(?i)(six sigma[\w\s\-/]{0,30})",
    ]
    certs = []
    for pattern in patterns:
        matches = re.findall(pattern, text)
        for m in matches:
            cert = m.strip()[:80]
            if cert and cert not in certs:
                certs.append(cert)
    return certs[:10]


def extract_years_experience(text: str) -> float:
    """Extract years of experience from text."""
    patterns = [
        r"(\d+)\+?\s*years?\s+(?:of\s+)?(?:professional\s+)?experience",
        r"(\d+)\+?\s*years?\s+in\s+(?:the\s+)?(?:\w+\s+)?(?:industry|field|sector|profession)",
        r"experience[:\s]+(\d+)\+?\s*years?",
        r"(\d+)\+?\s*yrs?\s+(?:of\s+)?(?:professional\s+)?experience",
    ]
    max_years = 0.0
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for m in matches:
            try:
                years = float(m)
                if 0 < years < 50:
                    max_years = max(max_years, years)
            except ValueError:
                pass
    # Fallback: count date ranges in work history (rough heuristic)
    if max_years == 0:
        year_pattern = r"\b(19[89]\d|20[012]\d)\b"
        years_found = [int(y) for y in re.findall(year_pattern, text)]
        if len(years_found) >= 2:
            import datetime
            current_year = datetime.datetime.now().year
            earliest = min(years_found)
            if earliest < current_year:
                max_years = min(float(current_year - earliest), 40.0)
    return max_years


def infer_seniority(text: str, years: float) -> str:
    text_lower = text.lower()
    # Check for explicit seniority keywords
    for level, keywords in SENIORITY_KEYWORDS.items():
        for kw in keywords:
            if re.search(r"\b" + re.escape(kw) + r"\b", text_lower):
                # executive and manager trump others
                if level in ("executive", "manager", "lead"):
                    return level
    # Use years of experience as fallback
    if years >= 15:
        return "senior"
    elif years >= 8:
        return "senior"
    elif years >= 4:
        return "mid"
    elif years >= 1:
        return "junior"
    else:
        return "mid"


def extract_industries(text: str) -> list[str]:
    text_lower = text.lower()
    found = []
    for industry, keywords in INDUSTRY_KEYWORDS.items():
        for kw in keywords:
            if kw in text_lower:
                if industry not in found:
                    found.append(industry)
                break
    return found


def extract_location(text: str) -> str:
    text_lower = text.lower()
    for city in AUSTRALIAN_CITIES:
        if city.lower() in text_lower:
            return city.title()
    return ""


def infer_role_families(skills: list[str]) -> list[str]:
    skills_lower = {s.lower() for s in skills}
    family_scores: dict[str, int] = {}
    for family, keywords in ROLE_FAMILY_MAPPINGS.items():
        score = sum(1 for kw in keywords if kw.lower() in skills_lower)
        if score > 0:
            family_scores[family] = score
    sorted_families = sorted(family_scores.items(), key=lambda x: x[1], reverse=True)
    return [f for f, _ in sorted_families[:4]]


def extract_summary(text: str) -> str:
    """Extract a professional summary from the text."""
    patterns = [
        r"(?i)(?:professional\s+)?summary[:\s\n]+([\s\S]{50,500}?)(?:\n{2,}|\Z)",
        r"(?i)(?:career\s+)?(?:objective|profile|overview)[:\s\n]+([\s\S]{50,500}?)(?:\n{2,}|\Z)",
        r"(?i)about\s+me[:\s\n]+([\s\S]{50,500}?)(?:\n{2,}|\Z)",
    ]
    for pattern in patterns:
        m = re.search(pattern, text)
        if m:
            return m.group(1).strip()[:400]
    # First meaningful paragraph as fallback
    paragraphs = [p.strip() for p in text.split("\n\n") if len(p.strip()) > 80]
    if paragraphs:
        return paragraphs[0][:400]
    return ""


def parse_resume(file_bytes: bytes, content_type: str) -> CandidateProfile:
    raw_text = extract_text(file_bytes, content_type)
    if not raw_text.strip():
        return CandidateProfile(raw_text="")

    name = extract_name(raw_text)
    summary = extract_summary(raw_text)
    skills, tools = extract_skills_and_tools(raw_text)
    certifications = extract_certifications(raw_text)
    years = extract_years_experience(raw_text)
    seniority = infer_seniority(raw_text, years)
    industries = extract_industries(raw_text)
    location = extract_location(raw_text)
    role_families = infer_role_families(skills)

    # Domains = industries + role families for overlap
    domains = list(set(industries + role_families))

    return CandidateProfile(
        name=name,
        summary=summary,
        skills=skills,
        tools=tools,
        certifications=certifications,
        industries=industries,
        domains=domains,
        seniority=seniority,
        years_experience=years,
        role_families=role_families,
        location=location,
        raw_text=raw_text[:5000],  # trim to avoid bloat
    )
