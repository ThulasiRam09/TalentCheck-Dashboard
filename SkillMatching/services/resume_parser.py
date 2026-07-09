"""
resume_parser.py
----------------
Extracts structured skill data from PDF or DOCX resumes.

Approach
--------
1. Extract raw text from the file (pdfplumber for PDF, python-docx for DOCX).
2. Scan for a SKILLS section and pull skills listed there.
3. Run a keyword scan across the entire text using a curated master skill list
   to catch skills mentioned anywhere (e.g., inside project descriptions).
4. Merge, deduplicate, and categorize.

Design note
-----------
When teammates finish their Resume Parser module, replace the parse() method
call with a call to their API and map the response to ParsedResume.
The matching engine never needs to change.
"""

import re
import io
import logging
from pathlib import Path
from typing import Optional

import pdfplumber
from docx import Document

from services.schemas import ParsedResume

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# Master keyword lists used for scanning full resume text.
# These are broader than exact JD skills so we catch every possible mention.
# ──────────────────────────────────────────────────────────────────────────────

PROGRAMMING_LANGUAGES = [
    "python", "java", "c++", "c#", "c", "javascript", "js", "typescript", "ts",
    "r", "go", "golang", "rust", "kotlin", "swift", "scala", "perl", "ruby",
    "php", "bash", "shell", "matlab", "dart", "vba", "cobol", "fortran",
]

FRAMEWORKS = [
    "spring boot", "spring", "django", "flask", "fastapi", "express", "nestjs",
    "react", "reactjs", "angular", "angularjs", "vue", "vuejs", "next.js", "nuxt",
    "bootstrap", "tailwind", "jquery", "hibernate", "struts", "laravel",
    "tensorflow", "pytorch", "keras", "scikit-learn", "sklearn", "xgboost",
    "pandas", "numpy", "matplotlib", "seaborn", "plotly", "scipy", "huggingface",
    "langchain", "spark", "hadoop", "kafka", "airflow",
]

DATABASES = [
    "mysql", "postgresql", "postgres", "mongodb", "sqlite", "oracle", "sql server",
    "mssql", "redis", "cassandra", "dynamodb", "firebase", "elasticsearch",
    "neo4j", "mariadb", "couchdb", "hbase", "bigquery", "snowflake", "redshift",
]

CLOUD = [
    "aws", "amazon web services", "azure", "microsoft azure", "gcp",
    "google cloud", "heroku", "digitalocean", "cloudflare", "vercel", "netlify",
    "ec2", "s3", "lambda", "ecs", "eks", "rds", "sagemaker",
]

TOOLS_AND_TECHNOLOGIES = [
    "git", "github", "gitlab", "bitbucket", "docker", "kubernetes", "k8s",
    "jenkins", "github actions", "ci/cd", "terraform", "ansible", "linux",
    "unix", "bash", "powershell", "postman", "swagger", "jira", "confluence",
    "tableau", "power bi", "excel", "vs code", "intellij", "eclipse",
    "jupyter", "colab", "airflow", "grafana", "kibana", "prometheus",
    "rest api", "graphql", "soap", "oauth", "jwt", "microservices",
    "machine learning", "ml", "deep learning", "nlp", "computer vision",
    "data science", "data analysis", "data visualization", "statistics",
    "oop", "object oriented", "design patterns", "agile", "scrum", "devops",
]

CERTIFICATIONS_KEYWORDS = [
    "aws certified", "azure certified", "google certified", "certified",
    "certification", "comptia", "cisco", "pmp", "scrum master",
]

ALL_SKILLS = list({
    *PROGRAMMING_LANGUAGES,
    *FRAMEWORKS,
    *DATABASES,
    *CLOUD,
    *TOOLS_AND_TECHNOLOGIES,
})

# Sections that typically list skills in a resume
SKILL_SECTION_HEADERS = re.compile(
    r"(skills?|technical\s+skills?|core\s+competencies|technologies?|"
    r"tools?\s+&\s+technologies?|expertise|proficiency|key\s+skills?)",
    re.IGNORECASE,
)

# Section headers that signal the end of the skills section
SECTION_BOUNDARY = re.compile(
    r"^\s*(experience|employment|work\s+history|education|projects?|"
    r"certifications?|achievements?|awards?|publications?|interests?|"
    r"hobbies|references?|summary|objective|profile|contact)\s*$",
    re.IGNORECASE,
)


# ──────────────────────────────────────────────────────────────────────────────
# Text extraction helpers
# ──────────────────────────────────────────────────────────────────────────────

def _extract_text_from_pdf(file_bytes: bytes) -> str:
    text_parts = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
    return "\n".join(text_parts)


def _extract_text_from_docx(file_bytes: bytes) -> str:
    doc = Document(io.BytesIO(file_bytes))
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n".join(paragraphs)


def extract_raw_text(file_bytes: bytes, filename: str) -> str:
    """Dispatch to the right extractor based on file extension."""
    ext = Path(filename).suffix.lower()
    if ext == ".pdf":
        return _extract_text_from_pdf(file_bytes)
    elif ext in (".docx", ".doc"):
        return _extract_text_from_docx(file_bytes)
    else:
        raise ValueError(f"Unsupported file type: {ext}. Use PDF or DOCX.")


# ──────────────────────────────────────────────────────────────────────────────
# Name & email extraction
# ──────────────────────────────────────────────────────────────────────────────

def _extract_email(text: str) -> str:
    match = re.search(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", text)
    return match.group(0) if match else ""


def _extract_name(text: str) -> str:
    """
    Heuristic: the candidate name is usually on the first non-empty line,
    before any email / phone / LinkedIn text appears.
    """
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    for line in lines[:5]:
        # Skip lines that look like contact info
        if re.search(r"[@|•|\|]|\d{10}|linkedin|github|http", line, re.IGNORECASE):
            continue
        # Name lines are usually 2-4 words, all letters
        words = line.split()
        if 2 <= len(words) <= 4 and all(re.match(r"^[A-Za-z.'-]+$", w) for w in words):
            return line
    return "Unknown Candidate"


# ──────────────────────────────────────────────────────────────────────────────
# Skill extraction
# ──────────────────────────────────────────────────────────────────────────────

def _scan_for_skills(text: str) -> list[str]:
    """
    Scan the entire document text for known skill keywords.
    Returns a deduplicated list (lowercase).
    """
    text_lower = text.lower()
    found = []
    for skill in ALL_SKILLS:
        # Use word boundary matching so "r" doesn't match inside "azure"
        pattern = r"\b" + re.escape(skill) + r"\b"
        if re.search(pattern, text_lower):
            found.append(skill)
    return list(dict.fromkeys(found))  # preserve order, deduplicate


def _extract_skills_section(text: str) -> list[str]:
    """
    Try to find a dedicated Skills section and extract comma/bullet/newline
    separated skills from it.
    """
    lines = text.split("\n")
    in_skills_section = False
    skill_lines = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        if SKILL_SECTION_HEADERS.search(stripped) and len(stripped) < 60:
            in_skills_section = True
            continue

        if in_skills_section:
            if SECTION_BOUNDARY.match(stripped) and len(stripped) < 40:
                break
            skill_lines.append(stripped)

    raw = " ".join(skill_lines)
    # Split on commas, bullets, pipes, semicolons
    tokens = re.split(r"[,•|;\n]+", raw)
    skills = []
    for token in tokens:
        token = token.strip(" -–•·")
        # Remove rating info like "Python (Advanced)"
        token = re.sub(r"\(.*?\)", "", token).strip()
        if 2 <= len(token) <= 40:
            skills.append(token.lower())

    return skills


def _extract_education(text: str) -> list[str]:
    degrees = re.findall(
        r"(b\.?tech|b\.?e\.?|m\.?tech|m\.?e\.?|bca|mca|b\.?sc|m\.?sc|"
        r"bachelor|master|ph\.?d|diploma|associate)[^\n]{0,80}",
        text,
        re.IGNORECASE,
    )
    return [d.strip() for d in degrees]


def _extract_certifications(text: str) -> list[str]:
    certs = []
    for keyword in CERTIFICATIONS_KEYWORDS:
        matches = re.findall(
            keyword + r"[^\n]{0,60}", text, re.IGNORECASE
        )
        certs.extend([m.strip() for m in matches])
    return list(dict.fromkeys(certs))


def _extract_projects(text: str) -> list[str]:
    """Extract project titles (lines near 'Projects' heading)."""
    lines = text.split("\n")
    in_projects = False
    projects = []
    for line in lines:
        stripped = line.strip()
        if re.match(r"^\s*projects?\s*$", stripped, re.IGNORECASE):
            in_projects = True
            continue
        if in_projects:
            if SECTION_BOUNDARY.match(stripped) and len(stripped) < 40:
                break
            if stripped and len(stripped) < 80:
                projects.append(stripped)
    return projects[:10]  # cap at 10


def _categorize(skills: list[str]) -> tuple[list, list, list, list, list]:
    """Split a flat skill list into categories for richer output."""
    langs, frameworks, dbs, cloud, tools = [], [], [], [], []
    skills_lower = [s.lower() for s in skills]
    for s in skills_lower:
        if s in PROGRAMMING_LANGUAGES:
            langs.append(s)
        elif s in FRAMEWORKS:
            frameworks.append(s)
        elif s in DATABASES:
            dbs.append(s)
        elif s in CLOUD:
            cloud.append(s)
        else:
            tools.append(s)
    return langs, frameworks, dbs, cloud, tools


# ──────────────────────────────────────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────────────────────────────────────

def parse(file_bytes: bytes, filename: str) -> ParsedResume:
    """
    Main entry point.
    Accepts raw file bytes and filename, returns a ParsedResume object.

    Replacement contract (for teammate integration):
        Replace this function's body with an HTTP call to the Resume Parser API.
        Map their response to ParsedResume. The matching engine never changes.
    """
    raw_text = extract_raw_text(file_bytes, filename)

    # Extract name and email
    candidate_name = _extract_name(raw_text)
    email = _extract_email(raw_text)

    # Extract skills via two strategies then merge
    section_skills = _extract_skills_section(raw_text)
    scanned_skills = _scan_for_skills(raw_text)

    # Merge: prioritize section skills (likely more precise), then scan
    all_skills_raw = section_skills + [s for s in scanned_skills if s not in section_skills]
    all_skills = list(dict.fromkeys(all_skills_raw))  # dedup, preserve order

    # Categorize
    langs, frameworks, dbs, cloud, tools = _categorize(all_skills)

    return ParsedResume(
        candidate_name=candidate_name,
        email=email,
        skills=all_skills,
        programming_languages=langs,
        frameworks=frameworks,
        databases=dbs,
        cloud_skills=cloud,
        tools=tools,
        certifications=_extract_certifications(raw_text),
        education=_extract_education(raw_text),
        projects=_extract_projects(raw_text),
        raw_text=raw_text[:3000],  # truncate for storage
    )


def parse_from_path(file_path: str) -> ParsedResume:
    """Helper for loading resumes directly from the filesystem."""
    path = Path(file_path)
    with open(path, "rb") as f:
        return parse(f.read(), path.name)
