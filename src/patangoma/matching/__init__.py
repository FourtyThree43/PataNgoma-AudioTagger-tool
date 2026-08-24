"""Matching engine package for metadata intelligence."""

from patangoma.matching.matcher import (
    MatchingEngine,
    compute_artist_similarity,
    compute_duration_score,
    compute_string_similarity,
    compute_token_sort_similarity,
    normalize_text,
)

__all__ = [
    "MatchingEngine",
    "compute_artist_similarity",
    "compute_duration_score",
    "compute_string_similarity",
    "compute_token_sort_similarity",
    "normalize_text",
]
