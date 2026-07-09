"""
recommendation.py
-----------------
Generates actionable learning recommendations based on:
  - Missing skills from a JD
  - Partial match gaps
  - Priority (required skills > preferred skills)

Keeps recommendations short, clear, and relevant.
"""

from services.schemas import JobMatchResult, ParsedJD

# Priority resources for common skills
LEARNING_RESOURCES: dict[str, str] = {
    "docker": "Docker official docs → docs.docker.com",
    "kubernetes": "Kubernetes Learn → kubernetes.io/docs/tutorials",
    "aws": "AWS Free Tier + AWS Skill Builder",
    "azure": "Microsoft Learn → learn.microsoft.com",
    "gcp": "Google Cloud Skills Boost",
    "machine learning": "fast.ai or Andrew Ng's ML course (Coursera)",
    "deep learning": "fast.ai Part 2 or deeplearning.ai",
    "tensorflow": "TensorFlow tutorials → tensorflow.org",
    "pytorch": "PyTorch tutorials → pytorch.org",
    "python": "Python.org docs or 'Automate the Boring Stuff'",
    "sql": "SQLZoo or Mode Analytics SQL tutorial",
    "git": "Pro Git Book → git-scm.com/book",
    "react": "React official docs → react.dev",
    "spring boot": "Spring Guides → spring.io/guides",
    "java": "Oracle Java tutorials or MOOC.fi Java course",
    "data structures": "NeetCode.io or Striver's DSA Sheet",
    "rest api": "REST API Design best practices on REST API Tutorial",
    "ci/cd": "GitHub Actions docs or Jenkins tutorials",
    "linux": "Linux Journey → linuxjourney.com",
    "agile": "Scrum Guide → scrumguides.org",
}


def generate_recommendations(result: JobMatchResult, jd: ParsedJD) -> list[str]:
    """
    Build a list of recommendation strings for a job match result.
    Missing required skills are prioritized over preferred skills.
    """
    recommendations: list[str] = []

    # Priority 1: required skills that are missing
    required_set = set(s.lower() for s in jd.required_skills)
    priority_missing = [s for s in result.missing_skills if s.lower() in required_set]
    other_missing = [s for s in result.missing_skills if s.lower() not in required_set]

    for skill in priority_missing[:5]:
        rec = _build_recommendation(skill, is_required=True)
        recommendations.append(rec)

    for skill in other_missing[:3]:
        rec = _build_recommendation(skill, is_required=False)
        recommendations.append(rec)

    # Priority 2: partial matches — candidate is close, encourage deepening
    for pm in result.partial_matches[:2]:
        if pm.similarity < 90:
            recommendations.append(
                f"Deepen knowledge of '{pm.jd_skill.title()}' "
                f"(your '{pm.candidate_skill.title()}' is {pm.similarity:.0f}% similar)"
            )

    # Cap at 8 recommendations max
    return recommendations[:8]


def _build_recommendation(skill: str, is_required: bool) -> str:
    prefix = "⚠ Required:" if is_required else "Recommended:"
    resource = LEARNING_RESOURCES.get(skill.lower(), "")
    if resource:
        return f"{prefix} Learn {skill.title()} → {resource}"
    return f"{prefix} Learn {skill.title()}"


def attach_recommendations(results: list[JobMatchResult], jds: list[ParsedJD]) -> list[JobMatchResult]:
    """
    Attach recommendations to each JobMatchResult in-place.
    jds is in the same order as results.
    """
    jd_map: dict[tuple[str, str], ParsedJD] = {
        (jd.company, jd.role): jd for jd in jds
    }

    for result in results:
        jd = jd_map.get((result.company, result.role))
        if jd:
            result.recommendations = generate_recommendations(result, jd)

    return results
