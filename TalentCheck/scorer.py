from typing import Dict, List, Optional
try:
    from .models import SkillCategory, CandidateProfile, CompanySkillset, SkillsetGap
except ImportError:
    from models import SkillCategory, CandidateProfile, CompanySkillset, SkillsetGap

class TalentScorer:
    def __init__(self):
        self.skill_category_weights = {
            # Adjust these weights based on what's most important
            SkillCategory.CODING: 1.0,
            SkillCategory.DSA: 1.2,  # DSA is often weighted higher
            SkillCategory.OOD: 1.0,
            SkillCategory.APTITUDE: 0.8,
            SkillCategory.COMMUNICATION: 0.8,
            SkillCategory.AI: 0.9,
            SkillCategory.CLOUD: 0.9,
            SkillCategory.SQL: 1.0,
            SkillCategory.SWE: 1.0,
            SkillCategory.SYSTEM_DESIGN: 1.1,
            SkillCategory.NETWORKING: 0.8,
            SkillCategory.OS: 0.8,
            SkillCategory.OTHER: 0.5
        }
    
    def infer_skill_level(self, candidate: CandidateProfile, category: SkillCategory) -> int:
        """Infer candidate's skill level for a specific category, factoring in skills and certifications."""
        # Find skills in this category
        relevant_skills = [s for s in candidate.skills if s.category_code == category]
        
        # Calculate level based on number of skills and their confidence
        base_level = min(5, len(relevant_skills))  # Max base level from quantity
        
        # Boost based on confidence
        confidence_boost = 0
        for skill in relevant_skills:
            if skill.confidence == "high":
                confidence_boost += 2
            elif skill.confidence == "medium":
                confidence_boost += 1
        
        # Skills in high-value categories get bonus
        category_bonus = 0
        if category in [SkillCategory.DSA, SkillCategory.SYSTEM_DESIGN]:
            category_bonus = 1
            
        # Certifications boost (Adds +2 per matching certification, e.g. AWS boosts CLOUD)
        cert_boost = 0
        category_keywords = {
            SkillCategory.CLOUD: ["aws", "azure", "gcp", "cloud"],
            SkillCategory.CODING: ["python", "java", "c++", "javascript", "coding", "programmer"],
            SkillCategory.SQL: ["sql", "database", "postgres", "mysql", "oracle", "db"],
            SkillCategory.AI: ["ai", "machine learning", "ml", "tensorflow", "pytorch", "deep learning"],
            SkillCategory.SYSTEM_DESIGN: ["docker", "kubernetes", "devops", "system design", "architecture"],
            SkillCategory.DSA: ["data structures", "algorithms", "dsa"],
            SkillCategory.NETWORKING: ["network", "networking", "ccna"],
            SkillCategory.OS: ["linux", "unix", "windows", "operating system", "os"]
        }
        
        keywords = category_keywords.get(category, [])
        if candidate.certifications:
            for cert in candidate.certifications:
                if any(kw in cert.lower() for kw in keywords):
                    cert_boost += 2
        
        # Final level (cap at 10)
        level = min(10, base_level + (confidence_boost // 2) + category_bonus + cert_boost)
        return level
    
    def calculate_skillset_gaps(self, candidate: CandidateProfile, company: CompanySkillset) -> List[SkillsetGap]:
        """Calculate gaps between candidate and company requirements."""
        gaps = []
        
        for category, required_level in company.skillset_requirements.items():
            candidate_level = self.infer_skill_level(candidate, category)
            is_gap = candidate_level < required_level
            
            gaps.append(SkillsetGap(
                category_code=category,
                required_level=required_level,
                candidate_level=candidate_level,
                gap=is_gap
            ))
        
        return gaps
    
    def calculate_readiness_score(self, gaps: List[SkillsetGap], candidate: Optional[CandidateProfile] = None) -> float:
        """Calculate overall readiness score (0-100), incorporating internship and hackathon boosts."""
        if not gaps:
            return 0.0
        
        total_weight = 0
        weighted_score_sum = 0
        
        for gap in gaps:
            weight = self.skill_category_weights.get(gap.category_code, 1.0)
            total_weight += weight
            
            # How close is candidate to requirement?
            if gap.required_level == 0:
                score = 100
            else:
                # Calculate match percentage for this skill
                ratio = min(1.0, gap.candidate_level / gap.required_level)
                score = ratio * 100
            
            weighted_score_sum += score * weight
        
        base_score = weighted_score_sum / total_weight
        
        # Apply boosts from internships and hackathons if candidate profile is provided
        if candidate:
            # +3.0% boost per internship, capped at 10%
            internship_boost = min(10.0, len(candidate.internships) * 3.0)
            # +1.5% boost per hackathon, capped at 5%
            hackathon_boost = min(5.0, len(candidate.hackathons) * 1.5)
            
            base_score = min(100.0, base_score + internship_boost + hackathon_boost)
            
        return round(base_score, 2)
    
    def get_readiness_label(self, score: float) -> str:
        """Get human-readable readiness label."""
        if score >= 85:
            return "Ready"
        elif score >= 70:
            return "Almost Ready"
        elif score >= 50:
            return "Needs Work"
        else:
            return "Not Ready"
    
    def generate_recommendations(self, gaps: List[SkillsetGap]) -> List[str]:
        """Generate actionable recommendations based on gaps."""
        recommendations = []
        
        # Sort gaps by severity (largest gap first)
        sorted_gaps = sorted(gaps, key=lambda g: g.required_level - g.candidate_level, reverse=True)
        
        for gap in sorted_gaps[:5]:  # Top 5 recommendations
            if gap.gap:
                diff = gap.required_level - gap.candidate_level
                recommendations.append(
                    f"Improve {gap.category_code.value}: need {diff} level(s) higher "
                    f"(current: {gap.candidate_level}/10, required: {gap.required_level}/10)"
                )
        
        if not recommendations:
            recommendations.append("You meet all requirements! Great job!")
        else:
            # Add general recommendation if there are gaps
            recommendations.append("Consider taking relevant courses or gaining hands-on experience in the areas above.")
        
        return recommendations
    
    def generate_summary(self, score: float, label: str, gaps: List[SkillsetGap]) -> str:
        """Generate a summary text."""
        total_gaps = sum(1 for g in gaps if g.gap)
        if total_gaps == 0:
            return f"You're {label}! You meet or exceed all {len(gaps)} skillset requirements."
        else:
            return f"You're {label}. You have gaps in {total_gaps} out of {len(gaps)} skillset areas. Score: {score}/100"