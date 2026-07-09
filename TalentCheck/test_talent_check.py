"""Test script to verify Talent Check functionality."""

import sys
import json

# Reconfigure stdout to UTF-8 to prevent UnicodeEncodeError on Windows terminal
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

try:
    from TalentCheck.main import TalentCheck
    from TalentCheck.models import Skill, SkillCategory, CandidateProfile
except ImportError:
    # Fallback if executing directly inside the TalentCheck directory
    from main import TalentCheck
    from models import Skill, SkillCategory, CandidateProfile

def create_sample_candidate():
    """Create a sample candidate for testing."""
    return CandidateProfile(
        name="John Doe",
        email="john@example.com",
        education="BS Computer Science, Stanford University",
        skills=[
            Skill(skill_name="Python", category_code=SkillCategory.CODING, confidence="high"),
            Skill(skill_name="JavaScript", category_code=SkillCategory.CODING, confidence="medium"),
            Skill(skill_name="Data Structures", category_code=SkillCategory.DSA, confidence="high"),
            Skill(skill_name="Algorithms", category_code=SkillCategory.DSA, confidence="medium"),
            Skill(skill_name="AWS", category_code=SkillCategory.CLOUD, confidence="medium"),
            Skill(skill_name="SQL", category_code=SkillCategory.SQL, confidence="high"),
            Skill(skill_name="React", category_code=SkillCategory.SWE, confidence="medium"),
        ],
        hackathons=["Google Hackathon 2023", "AI Hackathon 2022"],
        internships=["SWE Intern @ Google"],
        certifications=["AWS Certified Developer"],
        preferred_roles=["Full Stack Developer", "Software Engineer"]
    )

def create_weak_candidate():
    """Create a weaker candidate for testing different results."""
    return CandidateProfile(
        name="Jane Smith",
        email="jane@example.com",
        education="BA Economics, NYU",
        skills=[
            Skill(skill_name="Excel", category_code=SkillCategory.OTHER, confidence="high"),
            Skill(skill_name="SQL", category_code=SkillCategory.SQL, confidence="medium"),
        ],
        hackathons=[],
        internships=["Data Analyst Intern @ Startup"],
        certifications=[],
        preferred_roles=["Data Analyst"]
    )

def test_talent_check():
    """Run comprehensive tests."""
    print("=" * 60)
    print("TALENT CHECK TEST")
    print("=" * 60)
    
    # Initialize
    talent_check = TalentCheck(data_dir="./test_data")
    
    # Print available companies
    print("\n📊 Available Companies:")
    for company in talent_check.get_available_companies():
        print(f"  • {company}")
    
    # Test with strong candidate
    print("\n" + "=" * 60)
    print("TEST 1: Strong Candidate vs Google (Includes AWS Certification & 1 Internship, 2 Hackathons)")
    print("=" * 60)
    
    strong_candidate = create_sample_candidate()
    result = talent_check.run_talent_check(strong_candidate, "Google")
    
    print(f"\n📝 Candidate: {result.candidate_name}")
    print(f"🏢 Company: {result.company}")
    print(f"📊 Score: {result.readiness_score}/100")
    print(f"🎯 Status: {result.overall_readiness}")
    print(f"\n📋 Summary: {result.summary}")
    
    print("\n📈 Skillset Breakdown:")
    for gap in result.skillset_gap:
        status = "❌ GAP" if gap.gap else "✅ MET"
        print(f"  {gap.category_code.value}: Required {gap.required_level}, "
              f"Candidate {gap.candidate_level} - {status}")
    
    if result.recommendations:
        print("\n💡 Recommendations:")
        for rec in result.recommendations:
            print(f"  • {rec}")
    
    # Test with weak candidate
    print("\n" + "=" * 60)
    print("TEST 2: Weak Candidate vs Oracle Financial Services Software")
    print("=" * 60)
    
    weak_candidate = create_weak_candidate()
    result = talent_check.run_talent_check(weak_candidate, "Oracle Financial Services Software")
    
    print(f"\n📝 Candidate: {result.candidate_name}")
    print(f"🏢 Company: {result.company}")
    print(f"📊 Score: {result.readiness_score}/100")
    print(f"🎯 Status: {result.overall_readiness}")
    print(f"\n📋 Summary: {result.summary}")
    
    print("\n📈 Skillset Breakdown:")
    for gap in result.skillset_gap[:5]:  # Show first 5
        status = "❌ GAP" if gap.gap else "✅ MET"
        print(f"  {gap.category_code.value}: Required {gap.required_level}, "
              f"Candidate {gap.candidate_level} - {status}")
    
    # Test frontend format
    print("\n" + "=" * 60)
    print("TEST 3: Frontend Format")
    print("=" * 60)
    
    frontend_data = talent_check.format_result_for_frontend(result)
    print(json.dumps(frontend_data, indent=2)[:500] + "...")
    
    print("\n✅ All tests completed!")

if __name__ == "__main__":
    test_talent_check()