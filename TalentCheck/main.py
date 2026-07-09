import json
from typing import Dict, Optional, Union
from pathlib import Path

try:
    from .models import CandidateProfile, CompanySkillset, TalentCheckResult, SkillCategory
    from .data_loader import DataLoader
    from .scorer import TalentScorer
except ImportError:
    from models import CandidateProfile, CompanySkillset, TalentCheckResult, SkillCategory
    from data_loader import DataLoader
    from scorer import TalentScorer

class TalentCheck:
    def __init__(self, data_dir: str = "./data"):
        self.data_loader = DataLoader(data_dir)
        self.scorer = TalentScorer()
        self.company_data = self.data_loader.load_company_skillsets()
    
    def get_available_companies(self) -> list:
        """Get list of available company names."""
        return list(self.company_data.keys())
    
    def get_company_requirements(self, company_name: str) -> Optional[Dict]:
        """Get a company's skillset requirements."""
        if company_name not in self.company_data:
            return None
        
        company = self.company_data[company_name]
        return {
            "company": company.company,
            "requirements": company.skillset_requirements
        }
    
    def run_talent_check(
        self,
        profile: Union[CandidateProfile, Dict],
        company_name: str
    ) -> TalentCheckResult:
        """
        Run the full talent check.
        
        Args:
            profile: Candidate profile (either CandidateProfile object or dict)
            company_name: Name of the company to check against
        
        Returns:
            TalentCheckResult with scores and gaps
        """
        # Convert profile dict to CandidateProfile if needed
        if isinstance(profile, dict):
            profile = self.data_loader.load_candidate_profile(profile)
        
        # Get company data
        if company_name not in self.company_data:
            raise ValueError(f"Company '{company_name}' not found. Available: {self.get_available_companies()}")
        
        company = self.company_data[company_name]
        
        # Calculate gaps
        gaps = self.scorer.calculate_skillset_gaps(profile, company)
        
        # Calculate score (factoring in internship and hackathon boosts)
        score = self.scorer.calculate_readiness_score(gaps, profile)
        
        # Get readiness label
        label = self.scorer.get_readiness_label(score)
        
        # Generate summary
        summary = self.scorer.generate_summary(score, label, gaps)
        
        # Generate recommendations
        recommendations = self.scorer.generate_recommendations(gaps)
        
        # Create result
        result = TalentCheckResult(
            company=company_name,
            candidate_name=profile.name,
            skillset_gap=gaps,
            readiness_score=score,
            overall_readiness=label,
            summary=summary,
            recommendations=recommendations
        )
        
        return result
    
    def run_talent_check_from_json(
        self,
        profile_json_path: str,
        company_name: str
    ) -> TalentCheckResult:
        """Run talent check from a JSON file path."""
        profile = self.data_loader.load_profile_from_json(profile_json_path)
        return self.run_talent_check(profile, company_name)
    
    def format_result_for_frontend(self, result: TalentCheckResult) -> Dict:
        """Format result for frontend display."""
        return {
            "company": result.company,
            "candidate_name": result.candidate_name,
            "readiness_score": result.readiness_score,
            "overall_readiness": result.overall_readiness,
            "summary": result.summary,
            "recommendations": result.recommendations,
            "skillset_gap": [
                {
                    "category": gap.category_code.value,
                    "required_level": gap.required_level,
                    "candidate_level": gap.candidate_level,
                    "gap": gap.gap,
                    "status": "Gap" if gap.gap else "Met"
                }
                for gap in result.skillset_gap
            ]
        }