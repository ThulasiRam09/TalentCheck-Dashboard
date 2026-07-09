"""
ranking.py
----------
Sorts a list of JobMatchResult by match_score descending.
Provides a summary of the top N results.

Kept intentionally simple so it can be swapped for
ML-based ranking later if needed.
"""

from services.schemas import JobMatchResult


def rank_results(results: list[JobMatchResult]) -> list[JobMatchResult]:
    """Sort job match results from highest to lowest match score."""
    return sorted(results, key=lambda r: r.match_score, reverse=True)


def get_top_matches(results: list[JobMatchResult], top_n: int = 3) -> list[JobMatchResult]:
    """Return the top N results after ranking."""
    return rank_results(results)[:top_n]


def build_eligibility_summary(results: list[JobMatchResult]) -> dict:
    """
    Return a summary dict grouping jobs by eligibility tier.
    Useful for a dashboard widget.
    """
    summary: dict[str, list[str]] = {
        "Highly Eligible": [],
        "Eligible": [],
        "Moderately Eligible": [],
        "Needs Improvement": [],
        "Not Eligible": [],
    }
    for r in results:
        label = r.eligibility
        entry = f"{r.company} – {r.role} ({r.match_score}%)"
        if label in summary:
            summary[label].append(entry)
        else:
            summary["Not Eligible"].append(entry)
    return summary
