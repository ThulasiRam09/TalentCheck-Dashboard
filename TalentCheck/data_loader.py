import json
from pathlib import Path
from typing import Dict, List
try:
    from .models import CompanySkillset, SkillCategory, CandidateProfile, Skill
except ImportError:
    from models import CompanySkillset, SkillCategory, CandidateProfile, Skill

class DataLoader:
    def __init__(self, data_dir: str = "./data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
    def load_company_skillsets(self, file_path: str = "talent_check_company_skillsets.json") -> Dict[str, CompanySkillset]:
        """Load company skillset requirements from JSON file."""
        full_path = self.data_dir / file_path
        
        if not full_path.exists():
            # Create default data if file doesn't exist
            return self._create_default_company_data()
        
        with open(full_path, 'r') as f:
            data = json.load(f)
        
        companies = {}
        for company_name, requirements in data.items():
            # Convert string category keys to SkillCategory enum
            skillset_req = {}
            for cat, level in requirements.items():
                try:
                    category = SkillCategory(cat)
                    skillset_req[category] = level
                except ValueError:
                    # Handle unknown categories
                    continue
            
            companies[company_name] = CompanySkillset(
                company=company_name,
                skillset_requirements=skillset_req
            )
        
        return companies
    
    def _create_default_company_data(self) -> Dict[str, CompanySkillset]:
        """Create sample company data for testing."""
        default_data = {
            "Google": {
                "COD": 8, "DSA": 9, "OOD": 8, "APTI": 7, "COMM": 7,
                "AI": 6, "CLOUD": 5, "SQL": 6, "SWE": 8, "SYSD": 8,
                "NETW": 5, "OS": 6
            },
            "Microsoft": {
                "COD": 7, "DSA": 7, "OOD": 8, "APTI": 6, "COMM": 8,
                "AI": 7, "CLOUD": 8, "SQL": 7, "SWE": 7, "SYSD": 7,
                "NETW": 6, "OS": 6
            },
            "Oracle Financial Services Software": {
                "COD": 6, "DSA": 6, "OOD": 6, "APTI": 5, "COMM": 7,
                "AI": 4, "CLOUD": 5, "SQL": 7, "SWE": 6, "SYSD": 5,
                "NETW": 5, "OS": 5
            }
        }
        
        # Save as JSON for future use
        self.save_company_data(default_data)
        
        return self.load_company_skillsets()
    
    def save_company_data(self, data: Dict):
        """Save company data to JSON file."""
        file_path = self.data_dir / "talent_check_company_skillsets.json"
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def load_candidate_profile(self, profile_data: Dict) -> CandidateProfile:
        """Load candidate profile from dictionary or JSON."""
        return CandidateProfile(**profile_data)
    
    def load_profile_from_json(self, json_path: str) -> CandidateProfile:
        """Load candidate profile from JSON file."""
        with open(json_path, 'r') as f:
            data = json.load(f)
        return self.load_candidate_profile(data)
    
    def load_profile_from_profile_builder_output(self, profile_json: Dict) -> CandidateProfile:
        """Load profile from the Profile Builder's output format."""
        # Convert skills to Skill objects
        skills = []
        for skill_data in profile_json.get("skills", []):
            if isinstance(skill_data, dict):
                skills.append(Skill(**skill_data))
            else:
                # If it's just a string, create a basic Skill
                skills.append(Skill(skill_name=skill_data, category_code=SkillCategory.OTHER))
        
        # Create candidate profile
        return CandidateProfile(
            name=profile_json.get("name", "Unknown"),
            email=profile_json.get("email", ""),
            education=profile_json.get("education", ""),
            skills=skills,
            hackathons=profile_json.get("hackathons", []),
            internships=profile_json.get("internships", []),
            certifications=profile_json.get("certifications", []),
            preferred_roles=profile_json.get("preferred_roles", []),
            cv_file=profile_json.get("cv_file", "")
        )