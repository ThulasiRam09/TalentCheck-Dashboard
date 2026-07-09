"""
ats.py
------
FastAPI router for all ATS Skill Matching endpoints.

Endpoints:
  POST /upload-resume    → Parse a resume, return structured JSON
  POST /match            → Upload resume, match against all JDs, return ranked results
  GET  /jobs             → Return all parsed JDs (loaded at startup)
  POST /match-from-json  → Accept skills as JSON (for teammate integration)
  POST /batch-match      → Match all resumes in /data/resumes/ against all JDs
"""

import logging
from typing import Optional

from fastapi import APIRouter, File, UploadFile, HTTPException, Body
from fastapi.responses import JSONResponse

from services.schemas import ParsedResume, ParsedJD, ATSResponse, ManualSkillInput
from services.resume_parser import parse as parse_resume
from services.jd_parser import parse as parse_jd
from services.skill_matcher import match_resume_to_jd
from services.recommendation import attach_recommendations
from services.ranking import rank_results, build_eligibility_summary
from utils.file_loader import (
    load_all_jd_files,
    load_all_resume_files,
    validate_extension,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ats", tags=["ATS Skill Matching"])

# ──────────────────────────────────────────────────────────────────────────────
# Module-level JD cache (loaded once at startup, refreshed on demand)
# ──────────────────────────────────────────────────────────────────────────────

_cached_jds: list[ParsedJD] = []


def _get_jds() -> list[ParsedJD]:
    """Return cached JDs, parsing from disk if cache is empty."""
    global _cached_jds
    if not _cached_jds:
        _cached_jds = _load_jds_from_disk()
    return _cached_jds


def _load_jds_from_disk() -> list[ParsedJD]:
    jd_files = load_all_jd_files()
    parsed = []
    for file_bytes, filename in jd_files:
        try:
            jd = parse_jd(file_bytes, filename)
            parsed.append(jd)
            logger.info("Parsed JD: %s – %s (%d skills)", jd.company, jd.role, len(jd.all_skills))
        except Exception as e:
            logger.error("Failed to parse JD %s: %s", filename, e)
    return parsed


def _run_full_match(resume: ParsedResume, jds: list[ParsedJD]) -> ATSResponse:
    """Core pipeline: match resume against all JDs, rank, attach recommendations."""
    results = [match_resume_to_jd(resume, jd) for jd in jds]
    results = rank_results(results)
    results = attach_recommendations(results, jds)

    return ATSResponse(
        candidate_name=resume.candidate_name,
        total_jobs_analyzed=len(jds),
        analysis=results,
    )


# ──────────────────────────────────────────────────────────────────────────────
# Endpoints
# ──────────────────────────────────────────────────────────────────────────────

@router.get("/jobs", summary="List all parsed Job Descriptions")
async def get_all_jobs():
    """
    Returns all JDs that have been parsed from /data/jds/.
    Refreshes from disk on each call (useful during development).
    """
    global _cached_jds
    _cached_jds = _load_jds_from_disk()  # always refresh

    if not _cached_jds:
        raise HTTPException(status_code=404, detail="No JD files found in /data/jds/")

    return {
        "total": len(_cached_jds),
        "jobs": [
            {
                "company": jd.company,
                "role": jd.role,
                "required_skills": jd.required_skills,
                "preferred_skills": jd.preferred_skills,
                "all_skills": jd.all_skills,
                "experience_level": jd.experience_level,
                "source_file": jd.source_file,
            }
            for jd in _cached_jds
        ],
    }


@router.post("/upload-resume", summary="Parse a resume and return structured data")
async def upload_resume(file: UploadFile = File(...)):
    """
    Upload a PDF or DOCX resume.
    Returns extracted skills, education, certifications, and projects.
    Does NOT run matching — use /match for that.
    """
    if not validate_extension(file.filename or ""):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Please upload a PDF or DOCX file.",
        )

    file_bytes = await file.read()

    try:
        parsed = parse_resume(file_bytes, file.filename or "resume.pdf")
    except Exception as e:
        logger.error("Resume parsing error: %s", e)
        raise HTTPException(status_code=422, detail=f"Could not parse resume: {str(e)}")

    return {
        "candidate_name": parsed.candidate_name,
        "email": parsed.email,
        "skills": parsed.skills,
        "programming_languages": parsed.programming_languages,
        "frameworks": parsed.frameworks,
        "databases": parsed.databases,
        "cloud_skills": parsed.cloud_skills,
        "tools": parsed.tools,
        "certifications": parsed.certifications,
        "education": parsed.education,
        "projects": parsed.projects,
        "total_skills_found": len(parsed.skills),
    }


@router.post("/match", summary="Upload resume and get ranked job matches")
async def match_resume(file: UploadFile = File(...)):
    """
    Upload a PDF or DOCX resume.
    Compares it against ALL available JDs and returns a ranked report.

    Response includes:
      - match_score (0-100)
      - eligibility label
      - matched_skills
      - missing_skills
      - partial_matches
      - additional_skills
      - recommendations
    """
    if not validate_extension(file.filename or ""):
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Please upload a PDF or DOCX file.",
        )

    file_bytes = await file.read()

    try:
        resume = parse_resume(file_bytes, file.filename or "resume.pdf")
    except Exception as e:
        logger.error("Resume parsing failed: %s", e)
        raise HTTPException(status_code=422, detail=f"Could not parse resume: {str(e)}")

    jds = _get_jds()
    if not jds:
        raise HTTPException(
            status_code=503,
            detail="No JDs are available. Please ensure /data/jds/ contains PDF/DOCX files.",
        )

    response = _run_full_match(resume, jds)
    return response


@router.post(
    "/match-from-json",
    summary="Match skills provided as JSON (for teammate integration)",
)
async def match_from_json(payload: ManualSkillInput):
    """
    Accept a candidate profile as JSON instead of a file upload.
    This is the integration endpoint for teammates' Resume Parser / Profile Builder.

    Replace /upload-resume workflow with this endpoint when integrating.
    """
    # Build a ParsedResume from the JSON payload
    resume = ParsedResume(
        candidate_name=payload.candidate_name,
        email=payload.email or "",
        skills=[s.lower() for s in payload.skills],
        education=payload.education or [],
        certifications=payload.certifications or [],
        projects=payload.projects or [],
    )

    jds = _get_jds()
    if not jds:
        raise HTTPException(status_code=503, detail="No JDs available.")

    response = _run_full_match(resume, jds)
    return response


@router.post("/batch-match", summary="Match ALL local resumes against ALL JDs (demo mode)")
async def batch_match():
    """
    Processes every resume in /data/resumes/ against every JD.
    Returns a list of ATS reports, one per candidate.
    Useful for hackathon demo and integration testing.
    """
    resume_files = load_all_resume_files()
    if not resume_files:
        raise HTTPException(
            status_code=404,
            detail="No resume files found in /data/resumes/",
        )

    jds = _get_jds()
    if not jds:
        raise HTTPException(status_code=503, detail="No JDs available.")

    all_reports = []
    for file_bytes, filename in resume_files:
        try:
            resume = parse_resume(file_bytes, filename)
            report = _run_full_match(resume, jds)
            all_reports.append(report)
            logger.info("Batch matched: %s", resume.candidate_name)
        except Exception as e:
            logger.error("Batch match failed for %s: %s", filename, e)
            all_reports.append({
                "error": str(e),
                "file": filename,
            })

    return {
        "total_candidates": len(resume_files),
        "total_jds": len(jds),
        "reports": all_reports,
    }


@router.get("/refresh-jds", summary="Force reload JDs from disk")
async def refresh_jds():
    """Re-parses all JD files from disk and updates the cache."""
    global _cached_jds
    _cached_jds = _load_jds_from_disk()
    return {
        "message": f"Refreshed {len(_cached_jds)} JDs from disk.",
        "jds": [f"{jd.company} – {jd.role}" for jd in _cached_jds],
    }
