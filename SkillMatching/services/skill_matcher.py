"""
skill_matcher.py
----------------
The core matching engine.

Given one ParsedResume and one ParsedJD, it produces a JobMatchResult.

Workflow per JD:
  1. For each JD skill, find the best match from candidate skills (all 3 tiers).
  2. Classify as:
       - Exact / Alias match (score == 100) → matched_skills
       - Fuzzy match (80 ≤ score < 100)     → partial_matches
       - No match (score < 80)              → missing_skills
  3. Compute match_score using weighted formula.
  4. Compute additional_skills (candidate has, JD doesn't require).
  5. Determine eligibility label.

FUZZY_THRESHOLD is configurable here. Default = 80.
"""

import logging
from typing import Optional

from services.schemas import ParsedResume, ParsedJD, JobMatchResult, PartialMatch
from services.similarity import compare_skills, best_match_score

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────────────────────────────────────

FUZZY_THRESHOLD: float = 80.0  # minimum score to count as partial match

ELIGIBILITY_BANDS = [
    (90.0, "Highly Eligible"),
    (75.0, "Eligible"),
    (60.0, "Moderately Eligible"),
    (40.0, "Needs Improvement"),
    (0.0,  "Not Eligible"),
]


# ──────────────────────────────────────────────────────────────────────────────
# Eligibility label
# ──────────────────────────────────────────────────────────────────────────────

def get_eligibility_label(score: float) -> str:
    for threshold, label in ELIGIBILITY_BANDS:
        if score >= threshold:
            return label
    return "Not Eligible"


# ──────────────────────────────────────────────────────────────────────────────
# Core match function
# ──────────────────────────────────────────────────────────────────────────────

def match_resume_to_jd(resume: ParsedResume, jd: ParsedJD) -> JobMatchResult:
    """
    Compare a single ParsedResume against a single ParsedJD.
    Returns a fully populated JobMatchResult.
    """
    jd_skills = jd.all_skills
    candidate_skills = resume.skills

    if not jd_skills:
        logger.warning("JD %s - %s has no skills extracted.", jd.company, jd.role)
        return JobMatchResult(
            company=jd.company,
            role=jd.role,
            match_score=0.0,
            eligibility="Not Eligible",
            matched_skills=[],
            missing_skills=[],
            partial_matches=[],
            additional_skills=candidate_skills,
            recommendations=[f"Learn {s.title()}" for s in jd_skills[:5]],
        )

    matched_skills: list[str] = []
    missing_skills: list[str] = []
    partial_matches: list[PartialMatch] = []

    # Track which candidate skills were "used" so we can compute additional_skills
    candidate_skills_used: set[str] = set()

    for jd_skill in jd_skills:
        best_score, best_candidate_skill = best_match_score(jd_skill, candidate_skills)

        if best_score == 100.0:
            # Perfect match (exact or alias)
            matched_skills.append(jd_skill)
            if best_candidate_skill:
                candidate_skills_used.add(best_candidate_skill)

        elif best_score >= FUZZY_THRESHOLD:
            # Fuzzy / partial match
            partial_matches.append(PartialMatch(
                candidate_skill=best_candidate_skill or "",
                jd_skill=jd_skill,
                similarity=round(best_score, 1),
            ))
            # Count partial as a fractional match towards score
            # (handled below in scoring)
            if best_candidate_skill:
                candidate_skills_used.add(best_candidate_skill)

        else:
            missing_skills.append(jd_skill)

    # ── Scoring ────────────────────────────────────────────────────────────
    # Full points for exact matches, weighted points for partials
    total_jd = len(jd_skills)
    exact_weight = len(matched_skills) * 1.0
    partial_weight = sum(pm.similarity / 100.0 for pm in partial_matches)
    raw_score = ((exact_weight + partial_weight) / total_jd) * 100 if total_jd else 0
    match_score = round(min(raw_score, 100.0), 1)

    # ── Additional skills (candidate has but JD doesn't mention) ──────────
    additional_skills = [
        s for s in candidate_skills
        if s not in candidate_skills_used
    ]

    # ── Eligibility ────────────────────────────────────────────────────────
    eligibility = get_eligibility_label(match_score)

    return JobMatchResult(
        company=jd.company,
        role=jd.role,
        match_score=match_score,
        eligibility=eligibility,
        matched_skills=matched_skills,
        missing_skills=missing_skills,
        partial_matches=partial_matches,
        additional_skills=additional_skills,
        recommendations=[],  # filled by recommendation.py
    )
