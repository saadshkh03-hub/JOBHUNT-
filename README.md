# Resume Job Matcher AU

## What it does

Resume Job Matcher AU parses your resume (PDF, DOCX, or TXT), extracts your skills, seniority, industries, and role families, then searches real job boards concurrently and scores every result against your actual profile using a weighted engine. You get a ranked list split into "Strong Matches" (above your threshold, no blockers) and "Similar Jobs" (adjacent roles found via automatic search expansion), with a score breakdown showing exactly why each job did or did not match.

---

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+

### Backend setup

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env and add your Adzuna API keys (optional but recommended)
uvicorn main:app --reload --port 8000
```

The API will be running at http://localhost:8000. You can verify with:
```bash
curl http://localhost:8000/api/health
```

### Frontend setup

```bash
cd frontend
npm install
npm start
```

Open http://localhost:3000

---

## API Keys (Optional)

The app works without any API keys using APS Jobs (Australian Government) and Council job sources, but adding Adzuna dramatically expands the number of jobs searched.

**Adzuna** — free API keys:
1. Register at https://developer.adzuna.com/
2. Create an application to get an `app_id` and `app_key`
3. Add them to `backend/.env`:
   ```
   ADZUNA_APP_ID=your_app_id_here
   ADZUNA_APP_KEY=your_app_key_here
   ```

---

## Source Status

| Source | Status | Notes |
|--------|--------|-------|
| Adzuna | Fully implemented | Requires free API key from developer.adzuna.com |
| APS Jobs | Implemented with RSS + HTML fallback | Australian Government jobs (apsjobs.gov.au) |
| Council Jobs | Stub with aggregator fallback | Architecture ready; direct council URLs listed |
| Seek | Not implemented | No public API available |
| Indeed | Not implemented | No public API available |

---

## Running Tests

```bash
cd backend
pip install -r requirements.txt
pytest ../tests/ -v
```

Or from the project root:
```bash
cd backend && pytest ../tests/ -v
```

---

## Architecture

```
Resume Upload
     │
     ▼
┌─────────────────────┐
│   resume_parser.py  │  PDF/DOCX/TXT → CandidateProfile
│   (pdfplumber,      │  Skills, seniority, role families,
│    python-docx)     │  industries, location, years exp
└────────┬────────────┘
         │ CandidateProfile
         ▼
┌─────────────────────────────────────────────────────┐
│                   main.py (FastAPI)                  │
│                                                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────┐  │
│  │ Adzuna   │  │ APS Jobs │  │  Council Jobs    │  │
│  │ (real)   │  │ (RSS)    │  │  (aggregator)    │  │
│  └────┬─────┘  └────┬─────┘  └────────┬─────────┘  │
│       └─────────────┴─────────────────┘            │
│                     │ asyncio.gather                │
│                     ▼                               │
│           normalizer.py → deduplicate               │
│                     │                               │
│                     ▼                               │
│           scorer.py → ScoredJob[]                   │
│           (9-dimension weighted engine)             │
│                     │                               │
│                     ▼                               │
│   if strong_matches < threshold:                    │
│     similar_jobs.py → expand queries                │
│     → re-search → mark is_similar_job=True          │
│                     │                               │
│                     ▼                               │
│           SearchResponse (strong + similar)         │
└─────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────┐
│  React Frontend     │
│  SearchForm →       │
│  Results → JobCard  │
│  ScoreBreakdown     │
└─────────────────────┘
```

### Scoring Dimensions (weights sum to 100)

| Dimension | Weight | Description |
|-----------|--------|-------------|
| Skills Overlap | 25% | % of required skills candidate has |
| Title Relevance | 20% | Fuzzy match between job title and candidate role families |
| Preferred Skills | 10% | Bonus skills beyond minimum requirements |
| Seniority Alignment | 10% | Match between inferred job level and candidate seniority |
| Industry Relevance | 10% | Industry context match |
| Location Fit | 10% | Remote = 100%, same city = 100%, different = partial |
| Work Type Fit | 5% | Onsite/hybrid/remote match |
| Eligibility Fit | 5% | Citizenship/clearance requirement detection |
| Transferable Skills | 5% | Soft skills and cross-functional skills |

A job is a **Strong Match** when: `score >= strong_match_threshold` (default 70) AND no eligibility blockers.
