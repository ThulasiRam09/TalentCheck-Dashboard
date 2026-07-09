from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from enum import Enum

class SkillCategory(str, Enum):
    CODING = "COD"
    DSA = "DSA"
    OOD = "OOD"
    APTITUDE = "APTI"
    COMMUNICATION = "COMM"
    AI = "AI"
    CLOUD = "CLOUD"
    SQL = "SQL"
    SWE = "SWE"
    SYSTEM_DESIGN = "SYSD"
    NETWORKING = "NETW"
    OS = "OS"
    OTHER = "OTHER"

class Skill(BaseModel):
    skill_name: str
    category_code: SkillCategory
    evidence: str = ""
    confidence: str = "medium"  # high|medium|low

class CandidateProfile(BaseModel):
    name: str
    email: str
    education: str
    skills: List[Skill]
    hackathons: List[str] = []
    internships: List[str] = []
    certifications: List[str] = []
    preferred_roles: List[str] = []
    cv_file: str = ""

class CompanySkillset(BaseModel):
    company: str
    skillset_requirements: Dict[SkillCategory, int]  # 1-10 level

class SkillsetGap(BaseModel):
    category_code: SkillCategory
    required_level: int
    candidate_level: int
    gap: bool

class TalentCheckResult(BaseModel):
    company: str
    candidate_name: str
    skillset_gap: List[SkillsetGap]
    readiness_score: float  # 0-100
    overall_readiness: str  # "Ready", "Almost Ready", "Needs Work", "Not Ready"
    summary: Optional[str] = None
    recommendations: Optional[List[str]] = None