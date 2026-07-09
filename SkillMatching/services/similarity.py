"""
similarity.py
-------------
Three-tier skill comparison:
  1. Exact match      (case-insensitive)
  2. Fuzzy match      (RapidFuzz token_sort_ratio, threshold configurable)
  3. Alias / synonym  (hand-crafted lookup for very common tech abbreviations)

All public functions return a float 0-100 representing similarity.
The matching engine in skill_matcher.py is the only consumer.
"""

from rapidfuzz import fuzz
from typing import Optional

# ──────────────────────────────────────────────────────────────
# Synonym / alias map
# Key   = canonical form (lower-cased)
# Value = set of aliases that should be treated as equivalent
# ──────────────────────────────────────────────────────────────
SKILL_ALIASES: dict[str, set[str]] = {
    "javascript": {"js", "java script", "ecmascript", "es6", "es2015"},
    "typescript": {"ts"},
    "python": {"py"},
    "sql": {"mysql", "postgresql", "postgres", "mssql", "oracle sql", "pl/sql", "t-sql", "sqlite"},
    "machine learning": {"ml", "machine-learning"},
    "artificial intelligence": {"ai"},
    "deep learning": {"dl"},
    "natural language processing": {"nlp"},
    "object oriented programming": {"oop", "object-oriented", "oops"},
    "spring boot": {"spring", "spring framework", "springboot"},
    "react": {"reactjs", "react.js"},
    "node": {"nodejs", "node.js"},
    "angular": {"angularjs", "angular.js"},
    "vue": {"vuejs", "vue.js"},
    "kubernetes": {"k8s"},
    "docker": {"containerization", "containers"},
    "amazon web services": {"aws"},
    "google cloud platform": {"gcp"},
    "microsoft azure": {"azure"},
    "rest api": {"rest", "restful", "restful api", "rest apis"},
    "graphql": {"graph ql"},
    "ci/cd": {"ci cd", "continuous integration", "continuous deployment", "devops pipeline"},
    "git": {"github", "gitlab", "version control"},
    "linux": {"unix", "bash scripting", "shell scripting"},
    "data structures": {"dsa", "data structures and algorithms"},
    "microsoft excel": {"excel", "ms excel", "advanced excel"},
    "power bi": {"powerbi", "power-bi"},
    "tableau": {"tableau desktop"},
}

# Build reverse map: alias → canonical
_ALIAS_TO_CANONICAL: dict[str, str] = {}
for canonical, aliases in SKILL_ALIASES.items():
    _ALIAS_TO_CANONICAL[canonical] = canonical   # canonical maps to itself
    for alias in aliases:
        _ALIAS_TO_CANONICAL[alias] = canonical


def _normalize(skill: str) -> str:
    """Lower-case and strip whitespace."""
    return skill.strip().lower()


def resolve_canonical(skill: str) -> str:
    """
    Return the canonical form of a skill if one exists,
    otherwise return the normalized skill itself.
    """
    norm = _normalize(skill)
    return _ALIAS_TO_CANONICAL.get(norm, norm)


def exact_match(skill_a: str, skill_b: str) -> float:
    """
    Returns 100.0 if the two skills are exactly equal (case-insensitive),
    otherwise 0.0.
    """
    if _normalize(skill_a) == _normalize(skill_b):
        return 100.0
    return 0.0


def alias_match(skill_a: str, skill_b: str) -> float:
    """
    Returns 100.0 if both skills resolve to the same canonical term,
    otherwise 0.0.
    This catches SQL == MySQL, OOP == Object Oriented Programming, etc.
    """
    if resolve_canonical(skill_a) == resolve_canonical(skill_b):
        return 100.0
    return 0.0


def fuzzy_match(skill_a: str, skill_b: str) -> float:
    """
    Uses RapidFuzz token_sort_ratio which handles word-order differences
    and partial overlaps well.
    Returns a float 0-100.
    """
    return fuzz.token_sort_ratio(_normalize(skill_a), _normalize(skill_b))


def compare_skills(skill_a: str, skill_b: str) -> float:
    """
    Master comparison function.
    Runs all three tiers and returns the highest similarity found.

    Priority:
      exact / alias → 100 (stop early)
      fuzzy         → fuzz ratio 0-100
    """
    # Tier 1: exact
    if exact_match(skill_a, skill_b) == 100.0:
        return 100.0

    # Tier 2: alias/synonym
    if alias_match(skill_a, skill_b) == 100.0:
        return 100.0

    # Tier 3: fuzzy
    return fuzzy_match(skill_a, skill_b)


def best_match_score(candidate_skill: str, jd_skills: list[str]) -> tuple[float, Optional[str]]:
    """
    Given one candidate skill, find the best matching JD skill.

    Returns:
        (best_score, best_jd_skill_or_None)
    """
    best_score = 0.0
    best_match = None

    for jd_skill in jd_skills:
        score = compare_skills(candidate_skill, jd_skill)
        if score > best_score:
            best_score = score
            best_match = jd_skill

    return best_score, best_match
