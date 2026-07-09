"""
jd_parser.py
------------
Extracts structured skill data from PDF or DOCX Job Description files.

Approach
--------
1. Extract raw text from PDF/DOCX.
2. Identify company and role from filename (reliable) or first few lines.
3. Scan for Required / Preferred / Qualifications sections.
4. Run a keyword scan across the full text using the master skill list.
5. Merge and deduplicate into all_skills (used by matching engine).

Design note
-----------
When teammates finish their JD Analytics module, replace parse() with
a call to their API and map the response to ParsedJD.
"""

import re
import io
import logging
from pathlib import Path

import pdfplumber
from docx import Document

from services.schemas import ParsedJD
from services.resume_parser import (
    ALL_SKILLS,
    SKILL_SECTION_HEADERS,
    SECTION_BOUNDARY,
    _extract_text_from_pdf,
    _extract_text_from_docx,
)

logger = logging.getLogger(__name__)

# Section headers common in JDs that indicate skill lists
JD_REQUIRED_HEADERS = re.compile(
    r"(required\s+(skills?|qualifications?|experience)|"
    r"must\s+have|minimum\s+qualifications?|"
    r"basic\s+qualifications?|responsibilities)",
    re.IGNORECASE,
)

JD_PREFERRED_HEADERS = re.compile(
    r"(preferred\s+(skills?|qualifications?)|"
    r"good\s+to\s+have|nice\s+to\s+have|"
    r"preferred\s+experience|bonus)",
    re.IGNORECASE,
)

EXPERIENCE_PATTERN = re.compile(
    r"(\d+[\+]?\s*(?:to\s*\d+)?\s+years?\s+(?:of\s+)?(?:experience|exp))",
    re.IGNORECASE,
)

# ──────────────────────────────────────────────────────────────────────────────
# Filename-based company/role extraction
# Files are named like "Google LLC - Software Engineer.pdf"
# ──────────────────────────────────────────────────────────────────────────────

COMPANY_ROLE_MAP = {
    "google": "Google LLC",
    "microsoft": "Microsoft",
    "oracle": "Oracle Financial Services Software",
}

ROLE_ALIASES = {
    "software engineer": "Software Engineer",
    "data scientist": "Data Scientist",
    "data analyst": "Data Analyst",
    "associate software engineer": "Associate Software Engineer",
    "application support analyst": "Application Support Analyst",
}


def _parse_filename(filename: str) -> tuple[str, str]:
    """
    Extract company and role from filename.
    Expected pattern: 'CompanyName - Role Title.pdf'
    """
    stem = Path(filename).stem  # e.g. "Google LLC - Software Engineer"
    if " - " in stem:
        parts = stem.split(" - ", 1)
        company_raw = parts[0].strip()
        role_raw = parts[1].strip()
    else:
        company_raw = "Unknown Company"
        role_raw = stem

    # Normalize company name
    company = company_raw
    for key, canonical in COMPANY_ROLE_MAP.items():
        if key in company_raw.lower():
            company = canonical
            break

    # Normalize role name
    role = role_raw
    for key, canonical in ROLE_ALIASES.items():
        if key in role_raw.lower():
            role = canonical
            break

    return company, role


# ──────────────────────────────────────────────────────────────────────────────
# Section-based extraction
# ──────────────────────────────────────────────────────────────────────────────

def _extract_section(lines: list[str], header_pattern: re.Pattern) -> list[str]:
    """Extract bullet-point items under a matching section header."""
    in_section = False
    items = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        if header_pattern.search(stripped) and len(stripped) < 80:
            in_section = True
            continue

        if in_section:
            # Stop at next major section header
            if (JD_REQUIRED_HEADERS.search(stripped) or
                    JD_PREFERRED_HEADERS.search(stripped) or
                    SECTION_BOUNDARY.match(stripped)) and len(stripped) < 80:
                if not header_pattern.search(stripped):
                    break
            items.append(stripped)

    return items


def _parse_skill_tokens(lines: list[str]) -> list[str]:
    """
    Convert free-text lines into individual skill tokens.
    Handles comma-separated, bullet-separated, and newline-separated lists.
    """
    skills = []
    for line in lines:
        # Remove bullet characters
        line = re.sub(r"^[\s\-–•·*]+", "", line)
        # Split on commas or semicolons
        tokens = re.split(r"[,;]", line)
        for token in tokens:
            token = token.strip()
            # Remove trailing clarifications in parentheses
            token = re.sub(r"\(.*?\)", "", token).strip()
            # Remove leading "experience with/in", "knowledge of", etc.
            token = re.sub(
                r"^(experience\s+(with|in|of)\s+|knowledge\s+of\s+|"
                r"proficiency\s+in\s+|familiarity\s+with\s+|strong\s+|"
                r"ability\s+to\s+|understanding\s+of\s+)",
                "", token, flags=re.IGNORECASE
            ).strip()
            if 2 <= len(token) <= 60:
                skills.append(token.lower())
    return skills


def _scan_for_skills(text: str) -> list[str]:
    """Keyword scan across entire JD text using master skill list."""
    text_lower = text.lower()
    found = []
    for skill in ALL_SKILLS:
        pattern = r"\b" + re.escape(skill) + r"\b"
        if re.search(pattern, text_lower):
            found.append(skill)
    return list(dict.fromkeys(found))


def _extract_experience(text: str) -> str:
    match = EXPERIENCE_PATTERN.search(text)
    return match.group(1) if match else ""


# ──────────────────────────────────────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────────────────────────────────────

def parse(file_bytes: bytes, filename: str) -> ParsedJD:
    """
    Main entry point.
    Accepts raw file bytes and filename, returns a ParsedJD object.

    Replacement contract (for teammate integration):
        Replace this function's body with an HTTP call to the JD Analytics API.
        Map their response to ParsedJD. The matching engine never changes.
    """
    ext = Path(filename).suffix.lower()
    if ext == ".pdf":
        raw_text = _extract_text_from_pdf(file_bytes)
    elif ext in (".docx", ".doc"):
        raw_text = _extract_text_from_docx(file_bytes)
    else:
        raise ValueError(f"Unsupported file type: {ext}")

    company, role = _parse_filename(filename)
    lines = raw_text.split("\n")

    # Extract by section
    required_lines = _extract_section(lines, JD_REQUIRED_HEADERS)
    preferred_lines = _extract_section(lines, JD_PREFERRED_HEADERS)

    required_skills_raw = _parse_skill_tokens(required_lines)
    preferred_skills_raw = _parse_skill_tokens(preferred_lines)

    # Filter section-parsed skills to only short, plausible skill tokens (≤ 40 chars)
    # This prevents full sentences from narrative-style JDs polluting the skill list
    def _is_valid_skill_token(s: str) -> bool:
        return len(s) <= 40 and len(s.split()) <= 5

    required_skills = [s for s in required_skills_raw if _is_valid_skill_token(s)]
    preferred_skills = [s for s in preferred_skills_raw if _is_valid_skill_token(s)]

    # Full-text keyword scan — always clean, single-term skills
    scanned = _scan_for_skills(raw_text)

    # all_skills = keyword scan (gold standard) + any valid section tokens not already included
    section_extras = [
        s for s in required_skills + preferred_skills
        if s not in scanned
    ]
    all_skills_set = list(dict.fromkeys(scanned + section_extras))

    # Technologies = just the scanned list (factual keyword mentions)
    technologies = scanned

    experience = _extract_experience(raw_text)

    return ParsedJD(
        company=company,
        role=role,
        required_skills=required_skills,
        preferred_skills=preferred_skills,
        technologies=technologies,
        experience_level=experience,
        all_skills=all_skills_set,
        source_file=filename,
    )


def parse_from_path(file_path: str) -> ParsedJD:
    """Helper for loading JDs directly from the filesystem."""
    path = Path(file_path)
    with open(path, "rb") as f:
        return parse(f.read(), path.name)
