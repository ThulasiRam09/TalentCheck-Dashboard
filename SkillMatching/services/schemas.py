"""
schemas.py
----------
All Pydantic models used throughout the ATS Skill Matching backend.
These are the single source of truth for data shapes.
"""

from pydantic import BaseModel, Field
from typing import List, Optional


# ─────────────────────────────────────────────
# Skill atom
# ─────────────────────────────────────────────
class Skill(BaseModel):
    skill_name: str
    category: Optional[str] = "general"    # e.g. language, framework, tool, cloud


# ─────────────────────────────────────────────
# Parsed Resume
# ─────────────────────────────────────────────
class ParsedResume(BaseModel):
    candidate_name: str = ""
    email: Optional[str] = ""
    education: List[str] = Field(default_factory=list)
    skills: List[str] = Field(default_factory=list)          # flat list, ready for matching
    programming_languages: List[str] = Field(default_factory=list)
    frameworks: List[str] = Field(default_factory=list)
    databases: List[str] = Field(default_factory=list)
    cloud_skills: List[str] = Field(default_factory=list)
    tools: List[str] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)
    projects: List[str] = Field(default_factory=list)
    raw_text: Optional[str] = ""


# ─────────────────────────────────────────────
# Parsed JD
# ─────────────────────────────────────────────
class ParsedJD(BaseModel):
    company: str
    role: str
    required_skills: List[str] = Field(default_factory=list)
    preferred_skills: List[str] = Field(default_factory=list)
    technologies: List[str] = Field(default_factory=list)
    experience_level: Optional[str] = ""
    all_skills: List[str] = Field(default_factory=list)      # merged deduplicated list used for matching
    source_file: Optional[str] = ""


# ─────────────────────────────────────────────
# Skill Match result for a single JD
# ─────────────────────────────────────────────
class PartialMatch(BaseModel):
    candidate_skill: str
    jd_skill: str
    similarity: float


class JobMatchResult(BaseModel):
    company: str
    role: str
    match_score: float                           # 0-100 rounded to 1 decimal
    eligibility: str                             # label based on score
    matched_skills: List[str] = Field(default_factory=list)
    missing_skills: List[str] = Field(default_factory=list)
    partial_matches: List[PartialMatch] = Field(default_factory=list)
    additional_skills: List[str] = Field(default_factory=list)   # candidate has, JD doesn't need
    recommendations: List[str] = Field(default_factory=list)


# ─────────────────────────────────────────────
# Final ATS response
# ─────────────────────────────────────────────
class ATSResponse(BaseModel):
    candidate_name: str
    total_jobs_analyzed: int
    analysis: List[JobMatchResult]


# ─────────────────────────────────────────────
# API request bodies
# ─────────────────────────────────────────────
class ManualSkillInput(BaseModel):
    """
    Allow teammates to POST candidate skills directly as JSON
    instead of uploading a file, without changing the matching engine.
    """
    candidate_name: str
    skills: List[str]
    email: Optional[str] = ""
    education: Optional[List[str]] = Field(default_factory=list)
    certifications: Optional[List[str]] = Field(default_factory=list)
    projects: Optional[List[str]] = Field(default_factory=list)
