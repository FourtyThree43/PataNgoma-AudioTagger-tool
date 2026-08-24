"""Unit tests for MetadataAggregator service."""

from __future__ import annotations

from unittest.mock import MagicMock

from patangoma.domain.models import MetadataCandidate, TrackMetadata
from patangoma.services.aggregator import MetadataAggregator


def test_aggregator_multi_search_and_merge():
    cand_sp = MetadataCandidate(
        provider_name="spotify",
        provider_id="sp-1",
        title="Suzanna",
        artists=["Sauti Sol"],
        album="Midnight Train",
        genres=["Afro-Pop"],
        popularity=80,
        artwork_url="https://spotify.com/art.jpg",
    )
    cand_mb = MetadataCandidate(
        provider_name="musicbrainz",
        provider_id="mb-1",
        title="Suzanna",
        artists=["Sauti Sol"],
        year=2020,
        genres=["Kenyan Pop"],
        isrc="KE1234567890",
        mb_trackid="mb-track-uuid",
    )

    prov1 = MagicMock()
    prov1.name = "spotify"
    prov1.search_tracks.return_value = [cand_sp]

    prov2 = MagicMock()
    prov2.name = "musicbrainz"
    prov2.search_tracks.return_value = [cand_mb]

    aggregator = MetadataAggregator(providers=[prov1, prov2])

    track = TrackMetadata(
        file_path="/music/suzanna.mp3",
        title="Suzanna",
        artist="Sauti Sol",
    )

    best_match, all_ranked = aggregator.find_best_match(track)
    assert best_match is not None
    assert len(all_ranked) == 2

    # Test candidate field merging / conflict resolution
    merged = aggregator.merge_candidates(cand_sp, [cand_mb])
    assert merged.title == "Suzanna"
    assert merged.isrc == "KE1234567890"
    assert merged.mb_trackid == "mb-track-uuid"
    assert merged.year == 2020
    assert "Afro-Pop" in merged.genres
    assert "Kenyan Pop" in merged.genres
