"""Property-based testing using Hypothesis for metadata normalization and matching."""

from __future__ import annotations

import math

from hypothesis import given
from hypothesis import strategies as st

from patangoma.domain.models import (
    ConfidenceLevel,
    MetadataCandidate,
    TrackMetadata,
)
from patangoma.matching.matcher import (
    MatchingEngine,
    compute_duration_score,
    compute_string_similarity,
    normalize_text,
)
from patangoma.services.planner import PlanEngine


@given(st.text())
def test_property_normalize_text_invariants(text: str):
    """normalize_text must never crash and must always return lowercase string without leading/trailing whitespace."""
    normalized = normalize_text(text)
    assert isinstance(normalized, str)
    assert normalized == normalized.strip()
    assert normalized == normalized.lower()


@given(st.text(), st.text())
def test_property_string_similarity_bounds_and_symmetry(a: str, b: str):
    """compute_string_similarity must always return a float between 0.0 and 1.0 and be symmetric."""
    score_ab = compute_string_similarity(a, b)
    score_ba = compute_string_similarity(b, a)

    assert 0.0 <= score_ab <= 1.0
    assert 0.0 <= score_ba <= 1.0
    assert math.isclose(score_ab, score_ba, rel_tol=1e-5)


@given(
    st.floats(min_value=0.0, max_value=36000.0, allow_nan=False, allow_infinity=False),
    st.floats(min_value=0.0, max_value=36000.0, allow_nan=False, allow_infinity=False),
)
def test_property_duration_score_bounds(dur_a: float, dur_b: float):
    """compute_duration_score must return a score in [0.0, 1.0]."""
    score, reason = compute_duration_score(dur_a, dur_b)
    assert 0.0 <= score <= 1.0
    assert isinstance(reason, str)


@given(
    st.text(min_size=1, max_size=50),
    st.text(min_size=1, max_size=50),
    st.text(min_size=1, max_size=50),
    st.text(min_size=1, max_size=50),
)
def test_property_plan_generation_safety(
    title_a: str,
    artist_a: str,
    title_b: str,
    artist_b: str,
):
    """PlanEngine must produce a valid TagPlan for arbitrary string metadata without raising exceptions."""
    track = TrackMetadata(
        file_path="/tmp/fake_track.mp3",
        title=title_a,
        artist=artist_a,
    )
    candidate = MetadataCandidate(
        provider_name="hypothesis_provider",
        provider_id="hyp-1",
        title=title_b,
        artists=[artist_b],
    )

    engine = MatchingEngine()
    result = engine.evaluate_match(track, candidate)
    assert 0.0 <= result.score.total_score <= 1.0
    assert isinstance(result.confidence, ConfidenceLevel)

    # Validate plan diffs
    diffs = []
    for track_field, cand_field in PlanEngine.COMPARABLE_FIELDS:
        old_v = getattr(track, track_field, None)
        new_v = getattr(candidate, cand_field, None)
        diffs.append((old_v, new_v))

    assert len(diffs) == len(PlanEngine.COMPARABLE_FIELDS)
