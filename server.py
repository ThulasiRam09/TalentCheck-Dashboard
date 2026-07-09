import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# Ensure local directories are in the Python search path
root_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(root_dir))
sys.path.insert(0, str(root_dir / "TalentCheck"))
sys.path.insert(0, str(root_dir / "JD" / "backend"))
sys.path.insert(0, str(root_dir / "ResumeParsing"))
sys.path.insert(0, str(root_dir / "SkillMatching"))

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("radix_talent_match_server")

# Load environment variables
load_dotenv(dotenv_path=root_dir / ".env")

# Import microservices elements
import google.generativeai as genai

from TalentCheck.main import TalentCheck
from TalentCheck.models import CandidateProfile, Skill as TCSkill

from ResumeParsing.src.prompt import build_resume_prompt
from ResumeParsing.src.validator import validate_resume_json

from JD.backend.app.models.response_model import JobDescriptionAnalysis
from JD.backend.app.services.prompt import build_analysis_prompt

from SkillMatching.services.schemas import ParsedResume, ParsedJD
from SkillMatching.services.skill_matcher import match_resume_to_jd
from SkillMatching.services.recommendation import attach_recommendations

app = FastAPI(
    title="RADIX Talent Match Unified API",
    description="Unified API server connecting JD Analytics, Resume Parsing, Profile Builder, Talent Check, and Skill Matching.",
    version="2.0.0"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize TalentCheck engine
try:
    # Use TalentCheck data directory
    talent_check_engine = TalentCheck(data_dir=str(root_dir / "TalentCheck" / "data"))
except Exception as e:
    logger.error(f"Failed to initialize TalentCheck engine: {e}")
    talent_check_engine = None

# Configure Gemini
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    logger.warning("GOOGLE_API_KEY is not set in environment or .env. Gemini endpoints will fail.")
else:
    genai.configure(api_key=api_key)

# --------------------------------------------------------------------------
# API Models
# --------------------------------------------------------------------------
class TextPayload(BaseModel):
    filename: str
    text: str

class CheckPayload(BaseModel):
    profile: dict
    company: str

class SkillMatchPayload(BaseModel):
    profile: dict
    jd: dict

# --------------------------------------------------------------------------
# Endpoints
# --------------------------------------------------------------------------

@app.get("/health")
def health():
    return {"status": "ok", "has_api_key": bool(api_key)}

@app.get("/api/companies")
def get_companies():
    """Get target companies and their expected skillset standards."""
    if not talent_check_engine:
        raise HTTPException(status_code=500, detail="TalentCheck engine not initialized.")
    
    companies = []
    for company_name in talent_check_engine.get_available_companies():
        reqs = talent_check_engine.get_company_requirements(company_name)
        companies.append({
            "name": company_name,
            "requirements": {cat.value: val for cat, val in reqs["requirements"].items()} if reqs else {}
        })
    return companies

@app.get("/api/profiles")
def get_profiles():
    """Get sample prefilled profiles for the frontend simulator."""
    # Return 3 standard sample candidate profiles mapping directly to the frontend model
    return [
        {
            "id": "john_doe",
            "name": "John Doe",
            "email": "john.doe@stanford.edu",
            "education": "BS Computer Science, Stanford University",
            "skills": [
                {"skill_name": "Python", "category_code": "COD", "confidence": "high"},
                {"skill_name": "JavaScript", "category_code": "COD", "confidence": "medium"},
                {"skill_name": "Data Structures", "category_code": "DSA", "confidence": "high"},
                {"skill_name": "Algorithms", "category_code": "DSA", "confidence": "medium"},
                {"skill_name": "AWS Cloud", "category_code": "CLOUD", "confidence": "medium"},
                {"skill_name": "SQL", "category_code": "SQL", "confidence": "high"},
                {"skill_name": "React Frontend", "category_code": "SWE", "confidence": "medium"},
            ],
            "hackathons": ["Stanford TreeHacks 2024", "Google Solution Challenge"],
            "internships": ["Software Engineer Intern @ Google", "Backend Intern @ Stripe"],
            "certifications": ["AWS Certified Developer Associate"],
            "preferred_roles": ["Backend Engineer", "Full Stack Developer"]
        },
        {
            "id": "jane_smith",
            "name": "Jane Smith",
            "email": "jane.smith@nyu.edu",
            "education": "BA Economics & Minor in CS, NYU",
            "skills": [
                {"skill_name": "Excel Data Modeling", "category_code": "OTHER", "confidence": "high"},
                {"skill_name": "Basic SQL Queries", "category_code": "SQL", "confidence": "medium"},
                {"skill_name": "Python Scripting", "category_code": "COD", "confidence": "low"},
            ],
            "hackathons": [],
            "internships": ["Data Analyst Intern @ Local Startup"],
            "certifications": [],
            "preferred_roles": ["Junior Data Analyst", "Business Analyst"]
        },
        {
            "id": "alice_johnson",
            "name": "Alice Johnson",
            "email": "alice.j@mit.edu",
            "education": "MS in Artificial Intelligence, MIT",
            "skills": [
                {"skill_name": "PyTorch", "category_code": "AI", "confidence": "high"},
                {"skill_name": "TensorFlow", "category_code": "AI", "confidence": "high"},
                {"skill_name": "Python", "category_code": "COD", "confidence": "high"},
                {"skill_name": "System Design", "category_code": "SYSTEM_DESIGN", "confidence": "medium"},
                {"skill_name": "Kubernetes", "category_code": "SYSTEM_DESIGN", "confidence": "low"},
            ],
            "hackathons": ["MIT HackMIT Winner", "NVIDIA AI Hackathon"],
            "internships": ["Research Intern @ OpenAI", "AI Engineer Intern @ Meta"],
            "certifications": ["Google Professional Machine Learning Engineer"],
            "preferred_roles": ["Machine Learning Engineer", "AI Researcher"]
        }
    ]

@app.post("/api/check")
def run_check(payload: CheckPayload):
    """Run TalentCheck evaluation dashboard scoring and gap analysis."""
    if not talent_check_engine:
        raise HTTPException(status_code=500, detail="TalentCheck engine not initialized.")
    
    try:
        # Construct CandidateProfile model
        profile_dict = payload.profile
        # Clean skills representation to conform to CandidateProfile expectations
        skills_raw = profile_dict.get("skills", [])
        skills_objs = []
        for s in skills_raw:
            skills_objs.append(TCSkill(
                skill_name=s.get("skill_name", ""),
                category_code=s.get("category_code", "OTHER"),
                confidence=s.get("confidence", "medium"),
                evidence=s.get("evidence", "")
            ))
        
        candidate = CandidateProfile(
            name=profile_dict.get("name", "Candidate"),
            email=profile_dict.get("email", ""),
            education=profile_dict.get("education", ""),
            skills=skills_objs,
            hackathons=profile_dict.get("hackathons", []),
            internships=profile_dict.get("internships", []),
            certifications=profile_dict.get("certifications", []),
            preferred_roles=profile_dict.get("preferred_roles", [])
        )
        
        result = talent_check_engine.run_talent_check(candidate, payload.company)
        return talent_check_engine.format_result_for_frontend(result)
        
    except ValueError as val_err:
        raise HTTPException(status_code=400, detail=str(val_err))
    except Exception as exc:
        logger.exception("TalentCheck scoring failed")
        raise HTTPException(status_code=500, detail=f"Scoring engine error: {exc}")

@app.post("/api/parse-resume")
def parse_resume(payload: TextPayload):
    """Parse resume text using Google Gemini 2.5 Flash and return a structured profile."""
    if not api_key:
        raise HTTPException(status_code=500, detail="Gemini API Key is missing on the server.")
    
    try:
        prompt = build_resume_prompt(payload.text, payload.filename)
        model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        model = genai.GenerativeModel(model_name)
        
        response = model.generate_content(
            prompt,
            generation_config={
                "temperature": 0.1,
                "response_mime_type": "application/json",
            },
        )
        
        if not response.text:
            raise ValueError("Empty response received from Gemini.")
        
        # Clean markdown wrappers if any
        cleaned = response.text.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()
        
        raw_json = json.loads(cleaned)
        validated_dict = validate_resume_json(raw_json, payload.filename)
        
        # Format education list of dicts to string
        edu_list = validated_dict.get("education", [])
        edu_str = ""
        if edu_list:
            edu_str = ", ".join([
                f"{e.get('degree', '')} in {e.get('field', '')} from {e.get('institution', '')} ({e.get('year', '')})".strip().replace(" in  from", "").replace(" ()", "")
                for e in edu_list
            ])
            if not edu_str.strip() and edu_list[0].get("institution"):
                edu_str = edu_list[0].get("institution")
        
        # Format experience list of dicts to string list of internships
        exp_list = validated_dict.get("experience", [])
        intern_list = []
        for exp in exp_list:
            intern_list.append(f"{exp.get('role', '')} @ {exp.get('organization', '')}".strip(" @"))
            
        # Format hackathons list of dicts to string list of hackathons
        hack_list_raw = validated_dict.get("hackathons", [])
        hack_list = []
        for h in hack_list_raw:
            hack_list.append(h.get("name", ""))
            
        # Format skills
        skills_raw = validated_dict.get("skills", [])
        skills_formatted = []
        for s in skills_raw:
            skills_formatted.append({
                "skill_name": s.get("skill_name", ""),
                "category_code": s.get("category_code", "OTHER"),
                "confidence": s.get("confidence", "medium"),
                "evidence": s.get("evidence", "")
            })
            
        return {
            "name": validated_dict.get("name", ""),
            "email": validated_dict.get("email", ""),
            "education": edu_str,
            "skills": skills_formatted,
            "hackathons": hack_list,
            "internships": intern_list,
            "certifications": validated_dict.get("certifications", []),
            "preferred_roles": validated_dict.get("preferred_roles", [])
        }
        
    except Exception as e:
        logger.exception("Resume parsing failed")
        raise HTTPException(status_code=500, detail=f"Failed to parse resume: {e}")

@app.post("/api/analyze-jd")
def analyze_jd(payload: TextPayload):
    """Analyze Job Description text using Google Gemini 2.5 Flash."""
    if not api_key:
        raise HTTPException(status_code=500, detail="Gemini API Key is missing on the server.")
    
    try:
        prompt = build_analysis_prompt(payload.text)
        model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        model = genai.GenerativeModel(model_name)
        
        response = model.generate_content(
            prompt,
            generation_config={
                "response_mime_type": "application/json",
                "temperature": 0.2,
            },
        )
        
        # Prefer parsed object or fallback
        parsed = getattr(response, "parsed", None)
        if isinstance(parsed, JobDescriptionAnalysis):
            return parsed.model_dump()
            
        cleaned = response.text.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()
        
        return json.loads(cleaned)
        
    except Exception as e:
        logger.exception("JD analysis failed")
        raise HTTPException(status_code=500, detail=f"Failed to analyze JD: {e}")

@app.post("/api/skill-match")
def skill_match(payload: SkillMatchPayload):
    """Perform ATS Skill Matching between candidate profile and analyzed JD."""
    try:
        # Build ParsedResume from profile dict
        profile = payload.profile
        skills_list = [s.get("skill_name", "") for s in profile.get("skills", [])]
        
        resume = ParsedResume(
            candidate_name=profile.get("name", "Candidate"),
            email=profile.get("email", ""),
            education=[profile.get("education", "")],
            skills=skills_list,
            certifications=profile.get("certifications", []),
            projects=profile.get("internships", []) + profile.get("hackathons", [])
        )
        
        # Build ParsedJD from jd dict
        jd_dict = payload.jd
        required_skills = jd_dict.get("skills", [])
        preferred_skills = jd_dict.get("technologies", []) + jd_dict.get("soft_skills", [])
        all_skills = list(set(required_skills + preferred_skills))
        
        jd = ParsedJD(
            company=jd_dict.get("company", "Target Company"),
            role=jd_dict.get("role", jd_dict.get("summary", "Target Role")[:30]),
            required_skills=required_skills,
            preferred_skills=preferred_skills,
            technologies=jd_dict.get("technologies", []),
            experience_level=jd_dict.get("experience", ""),
            all_skills=all_skills,
            source_file="uploaded_jd.txt"
        )
        
        # Run matching
        match_result = match_resume_to_jd(resume, jd)
        
        # Attach recommendations
        results = attach_recommendations([match_result], [jd])
        final_result = results[0]
        
        return final_result.model_dump()
        
    except Exception as e:
        logger.exception("Skill match calculation failed")
        raise HTTPException(status_code=500, detail=f"Matching engine error: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000)
