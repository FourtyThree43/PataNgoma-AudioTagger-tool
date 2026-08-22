"""Unit tests for MetadataReasoner."""

from __future__ import annotations

from patangoma.domain.models import (
    ConfidenceLevel,
    MatchResult,
    MetadataCandidate,
    ScoreBreakdown,
    TrackMetadata,
)
from patangoma.services.ai_reasoner import MetadataReasoner


def test_parse_filename_artist_title():
    reasoner = MetadataReasoner()

    res1 = reasoner.parse_filename("Burna Boy - Last Last (Official Audio).mp3")
    assert res1.suggested_artist == "Burna Boy"
    assert res1.suggested_title == "Last Last"
    assert res1.confidence == "HIGH"

    res2 = reasoner.parse_filename("04 - Wizkid - Essence [HQ].flac")
    assert res2.suggested_track_number == 4
    assert res2.suggested_artist == "Wizkid"
    assert res2.suggested_title == "Essence"

    res3 = reasoner.parse_filename("RandomTrackName_320kbps.mp3")
    assert res3.suggested_title == "RandomTrackName"


def test_explain_match():
    reasoner = MetadataReasoner()
    candidate = MetadataCandidate(
        provider_name="deezer",
        provider_id="dz-100",
        title="Rush",
        artists=["Ayra Starr"],
    )
    score = ScoreBreakdown(
        total_score=0.92,
        title_score=1.0,
        artist_score=1.0,
        breakdown_reasons=["Title exact match", "Artist exact match"],
    )
    match = MatchResult(
        candidate=candidate,
        score=score,
        confidence=ConfidenceLevel.EXACT,
    )

    explanation = reasoner.explain_match(match)
    assert "Ayra Starr" in explanation
    assert "Rush" in explanation
    assert "92.0%" in explanation
    assert "Title exact match" in explanation


def test_suggest_tag_improvements():
    reasoner = MetadataReasoner()
    track = TrackMetadata(
        file_path="/music/Drake - God's Plan.mp3",
        title=None,
        artist=None,
        year=None,
        has_artwork=False,
    )

    suggestions = reasoner.suggest_tag_improvements(track)
    assert len(suggestions) >= 3
    assert any("Inferred" in s for s in suggestions)
    assert any("year" in s for s in suggestions)
    assert any("artwork" in s for s in suggestions)
