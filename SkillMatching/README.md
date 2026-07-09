# RADIX Talent Match — ATS Skill Matching Backend
### Role 5 – Skill Matching Module

---

## What This Does

This module compares a candidate's resume against all 6 hackathon Job Descriptions and returns:

| Output | Description |
|---|---|
| **Match Score** | 0–100% based on skill overlap |
| **Eligibility** | Highly Eligible / Eligible / Moderately Eligible / Needs Improvement / Not Eligible |
| **Matched Skills** | Skills the candidate has that the JD needs |
| **Missing Skills** | Skills the JD needs that the candidate lacks |
| **Partial Matches** | Fuzzy matches (e.g. SQL ↔ MySQL, OOP ↔ Object Oriented) |
| **Additional Skills** | Candidate skills not required by the JD |
| **Recommendations** | Learning suggestions for missing skills |

---

## Project Structure

```
backend/
├── main.py                     ← FastAPI app entry point
├── requirements.txt
├── sample_data.json            ← Example requests & responses
│
├── data/
│   ├── jds/                    ← Put all 6 JD PDFs here
│   │   ├── Google LLC - Software Engineer.pdf
│   │   ├── Google LLC - Data Scientist.pdf
│   │   ├── Microsoft - Software Engineer.pdf
│   │   ├── Microsoft - Data Analyst.pdf
│   │   ├── Oracle - Associate Software Engineer.pdf
│   │   └── Oracle - Application Support Analyst.pdf
│   └── resumes/               ← Put candidate resumes here (PDF or DOCX)
│
├── services/
│   ├── schemas.py              ← All Pydantic models
│   ├── resume_parser.py        ← Extracts skills from PDF/DOCX resumes
│   ├── jd_parser.py            ← Extracts skills from PDF/DOCX JDs
│   ├── similarity.py           ← Exact + Alias + Fuzzy matching logic
│   ├── skill_matcher.py        ← Core matching engine
│   ├── recommendation.py       ← Generates learning suggestions
│   └── ranking.py              ← Sorts results by score
│
├── routes/
│   └── ats.py                  ← All API endpoints
│
└── utils/
    └── file_loader.py          ← File I/O helpers
```

---

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start the server
uvicorn main:app --reload --port 8000

# 3. Open Swagger UI
http://localhost:8000/docs
```

---

## API Endpoints

### `POST /ats/match`
**Main endpoint.** Upload a resume (PDF or DOCX), get back ranked match results for all 6 JDs.

```bash
curl -X POST http://localhost:8000/ats/match \
  -F "file=@/path/to/resume.pdf"
```

### `POST /ats/upload-resume`
Parse a resume and return structured JSON only (no matching).

### `GET /ats/jobs`
Returns all parsed JDs with their extracted skill lists.

### `POST /ats/match-from-json`
**For teammate integration.** Send candidate skills as JSON — no file upload needed.

```json
POST /ats/match-from-json
{
  "candidate_name": "Rohan Verma",
  "skills": ["python", "java", "sql", "machine learning", "git"],
  "email": "rohan@example.com"
}
```

### `POST /ats/batch-match`
Processes every resume in `/data/resumes/` against all JDs. Perfect for hackathon demo.

### `GET /ats/refresh-jds`
Force reload JD files from disk.

---

## How Matching Works

```
JD Skill ──► Exact Match?  ─── Yes ──► Score: 100  → matched_skills
                │
               No
                │
             Alias Match?  ─── Yes ──► Score: 100  → matched_skills
             (SQL==MySQL)
                │
               No
                │
             Fuzzy Match   ──► ≥80%  → partial_matches
             (RapidFuzz)   ──► <80%  → missing_skills
```

**Score Formula:**
```
score = (exact_matches + fuzzy_weight_sum) / total_jd_skills × 100
```

---

## Eligibility Bands

| Score | Label |
|---|---|
| 90–100 | Highly Eligible |
| 75–89 | Eligible |
| 60–74 | Moderately Eligible |
| 40–59 | Needs Improvement |
| 0–39 | Not Eligible |

---

## Teammate Integration

When your teammates finish their modules, you only need to change **one thing** per module:

### Resume Parser / Profile Builder teammate
Replace the file-upload flow with `POST /ats/match-from-json`:
```python
# Their module calls:
response = requests.post("http://localhost:8000/ats/match-from-json", json={
    "candidate_name": profile["name"],
    "skills": profile["skills"],
    "email": profile["email"]
})
```

### JD Analytics teammate
Replace `jd_parser.py`'s `parse()` function body with:
```python
def parse(file_bytes, filename):
    response = requests.get("http://jd-analytics-api/jd/" + filename)
    data = response.json()
    return ParsedJD(
        company=data["company"],
        role=data["role"],
        all_skills=data["skills"],
        required_skills=data.get("required_skills", []),
        preferred_skills=data.get("preferred_skills", []),
    )
```

**The matching engine in `skill_matcher.py` NEVER changes.**
