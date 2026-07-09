"""
response_model.py
------------------
Pydantic models describing the shape of data returned by the API.

`JobDescriptionAnalysis` mirrors exactly the JSON structure we ask
Gemini to produce, and is also the model returned to the frontend.
Using Pydantic here gives us free validation: if Gemini ever returns
a malformed shape, model construction will raise and we can surface
a clean 502 error instead of forwarding garbage to the client.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class JobDescriptionAnalysis(BaseModel):
    """Structured analytics extracted from a Job Description."""

    summary: str = Field(default="", description="Short summary of the job description")
    skills: List[str] = Field(default_factory=list, description="Hard/technical skills required")
    responsibilities: List[str] = Field(default_factory=list, description="Key job responsibilities")
    experience: str = Field(default="", description="Required years/level of experience")
    education: str = Field(default="", description="Required education qualifications")
    technologies: List[str] = Field(default_factory=list, description="Tools, frameworks, languages")
    soft_skills: List[str] = Field(default_factory=list, description="Soft/interpersonal skills")
    keywords: List[str] = Field(default_factory=list, description="Notable ATS-style keywords")
    seniority: str = Field(default="", description="e.g. Junior, Mid, Senior, Lead")
    job_type: str = Field(default="", description="e.g. Full-time, Contract, Internship, Remote")
    location: str = Field(default="", description="Job location, if mentioned")


class AnalyzeResponse(BaseModel):
    """Top-level API response envelope for POST /analyze."""

    success: bool = True
    filename: str
    analysis: JobDescriptionAnalysis


class ErrorResponse(BaseModel):
    """Standardized error envelope returned on any failure."""

    success: bool = False
    error: str
    detail: Optional[str] = None
