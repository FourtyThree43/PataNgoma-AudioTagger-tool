"""Unit tests for AlbumMatcher service."""

from __future__ import annotations

from patangoma.domain.models import MetadataCandidate, TrackMetadata
from patangoma.services.album_matcher import AlbumMatcher


def test_album_matcher_align_tracks():
    matcher = AlbumMatcher()

    t1 = TrackMetadata(
        file_path="/m/01.mp3", track_number=1, title="Track One", artist="Artist A"
    )
    t2 = TrackMetadata(
        file_path="/m/02.mp3", track_number=2, title="Track Two", artist="Artist A"
    )

    cand1 = MetadataCandidate(
        provider_name="itunes",
        provider_id="c1",
        title="Track One",
        artists=["Artist A"],
        track_number=1,
    )
    cand2 = MetadataCandidate(
        provider_name="itunes",
        provider_id="c2",
        title="Track Two",
        artists=["Artist A"],
        track_number=2,
    )

    matches, avg_score = matcher.align_tracks([t1, t2], [cand2, cand1])

    assert len(matches) == 2
    assert avg_score >= 0.8
    # Verify t1 was matched to cand1
    assert matches[0][0].track_number == 1
    assert matches[0][1].track_number == 1
