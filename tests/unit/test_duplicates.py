"""Unit tests for DuplicateDetector service."""

from __future__ import annotations

from patangoma.domain.models import TrackMetadata
from patangoma.services.duplicates import DuplicateDetector


def test_duplicate_detector():
    t1_flac = TrackMetadata(
        file_path="/music/flac/last_last.flac",
        file_format="flac",
        title="Last Last",
        artist="Burna Boy",
        duration_seconds=172.0,
        bitrate=1000000,
    )
    t1_mp3 = TrackMetadata(
        file_path="/music/mp3/last_last.mp3",
        file_format="mp3",
        title="Last Last",
        artist="Burna Boy",
        duration_seconds=172.5,
        bitrate=320000,
    )
    t2 = TrackMetadata(
        file_path="/music/suzanna.mp3",
        file_format="mp3",
        title="Suzanna",
        artist="Sauti Sol",
        duration_seconds=230.0,
        bitrate=320000,
    )

    dups = DuplicateDetector.find_duplicates([t1_flac, t1_mp3, t2])
    assert len(dups) == 1
    cluster = dups[0]
    # Lossless FLAC should be primary keeper
    assert cluster.primary_track.file_format == "flac"
    assert len(cluster.duplicate_tracks) == 1
    assert cluster.duplicate_tracks[0].file_format == "mp3"
