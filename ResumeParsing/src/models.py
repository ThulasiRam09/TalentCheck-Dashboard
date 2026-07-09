from typing import Literal
from pydantic import BaseModel, Field


CategoryCode = Literal[
    "DSA", "COD", "OOD", "APTI", "COMM", "AI",
    "CLOUD", "SQL", "SWE", "SYSD", "NETW", "OS", "OTHER"
]

Confidence = Literal["high", "medium", "low"]


class Skill(BaseModel):
    skill_name: str = Field(..., min_length=1)
    category_code: CategoryCode = "OTHER"
    evidence: str = ""
    confidence: Confidence = "medium"


class Education(BaseModel):
    institution: str = ""
    degree: str = ""
    field: str = ""
    year: str = ""
    evidence: str = ""


class Project(BaseModel):
    name: str = ""
    description: str = ""
    technologies: list[str] = []
    evidence: str = ""


class Experience(BaseModel):
    organization: str = ""
    role: str = ""
    duration: str = ""
    description: str = ""
    technologies: list[str] = []
    evidence: str = ""


class Hackathon(BaseModel):
    name: str = ""
    role: str = ""
    duration: str = ""
    description: str = ""
    technologies: list[str] = []
    evidence: str = ""


class ResumeParseResult(BaseModel):
    source_type: Literal["resume"] = "resume"
    source_file: str = ""

    company: str = ""
    role: str = ""

    name: str = ""
    email: str = ""
    phone: str = ""
    linkedin: str = ""
    github: str = ""

    education: list[Education] = []
    projects: list[Project] = []
    experience: list[Experience] = []
    certifications: list[str] = []
    hackathons: list[Hackathon] = []
    preferred_roles: list[str] = []

    skills: list[Skill] = []
    summary: str = ""