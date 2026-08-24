"""Unit tests for the explainable MatchingEngine."""

from __future__ import annotations

from patangoma.domain.models import (
    ConfidenceLevel,
    MetadataCandidate,
    TrackMetadata,
)
from patangoma.matching.matcher import (
    MatchingEngine,
    compute_duration_score,
    compute_string_similarity,
    compute_token_sort_similarity,
    normalize_text,
)


def test_normalize_text():
    assert normalize_text("Blinding Lights (Official Video)") == "blinding lights"
    assert normalize_text("Hotel California (Remastered 2013)") == "hotel california"
    assert normalize_text("Malaika (feat. Miriam Makeba)") == "malaika"
    assert normalize_text("  Sauti   Sol  ") == "sauti sol"


def test_compute_string_similarity():
    assert (
        compute_string_similarity("Midnight City", "Midnight City (Remastered)") == 1.0
    )
    assert compute_string_similarity("Hello", "World") < 0.3
    assert compute_string_similarity("", "") == 1.0
    # Token-sort reordering tolerance
    assert compute_string_similarity("Beatles, The", "The Beatles") == 1.0
    assert compute_string_similarity("Burn The Stage", "Stage The Burn") == 1.0


def test_compute_token_sort_similarity():
    assert (
        compute_token_sort_similarity("Starboy The Weeknd", "The Weeknd Starboy") == 1.0
    )
    assert compute_token_sort_similarity("Artist A", "Artist B") < 1.0


def test_compute_duration_score():
    score_exact, _msg_exact = compute_duration_score(240.0, 241.0)
    assert score_exact == 1.0

    score_close, _msg_close = compute_duration_score(200.0, 206.0)
    assert 0.6 <= score_close < 1.0

    score_far, _msg_far = compute_duration_score(200.0, 250.0)
    assert score_far == 0.0


def test_matching_engine_exact_match():
    engine = MatchingEngine()
    track = TrackMetadata(
        file_path="/music/song.mp3",
        title="Suzanna",
        artist="Sauti Sol",
        album="Midnight Train",
        duration_seconds=230.0,
    )
    candidate = MetadataCandidate(
        provider_name="spotify",
        provider_id="spot-1",
        title="Suzanna",
        artists=["Sauti Sol"],
        album="Midnight Train",
        duration_seconds=230.5,
    )

    result = engine.evaluate_match(track, candidate)
    assert result.confidence == ConfidenceLevel.EXACT
    assert result.is_acceptable is True
    assert result.score.total_score >= 0.95


def test_matching_engine_isrc_shortcut():
    engine = MatchingEngine()
    track = TrackMetadata(
        file_path="/music/song.mp3",
        title="Unknown Title",
        artist="Unknown Artist",
        isrc="USUM71703861",
    )
    candidate = MetadataCandidate(
        provider_name="musicbrainz",
        provider_id="mb-1",
        title="Despacito",
        artists=["Luis Fonsi"],
        isrc="USUM71703861",
    )

    result = engine.evaluate_match(track, candidate)
    assert result.confidence == ConfidenceLevel.EXACT
    assert result.score.total_score == 1.0


def test_matching_engine_rank_candidates():
    engine = MatchingEngine()
    track = TrackMetadata(
        file_path="/music/song.mp3",
        title="Shape of You",
        artist="Ed Sheeran",
    )
    cand_poor = MetadataCandidate(
        provider_name="deezer",
        provider_id="1",
        title="Completely Different Song",
        artists=["Another Artist"],
    )
    cand_good = MetadataCandidate(
        provider_name="deezer",
        provider_id="2",
        title="Shape of You (Acoustic)",
        artists=["Ed Sheeran"],
    )
    cand_exact = MetadataCandidate(
        provider_name="deezer",
        provider_id="3",
        title="Shape of You",
        artists=["Ed Sheeran"],
    )

    ranked = engine.rank_candidates(track, [cand_poor, cand_good, cand_exact])
    assert ranked[0].candidate.provider_id == "3"
    assert ranked[1].candidate.provider_id == "2"
    assert ranked[2].candidate.provider_id == "1"
