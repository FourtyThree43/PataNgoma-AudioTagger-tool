"""Unit tests for audio quality and transcode inspector."""

from pathlib import Path

from patangoma.services.quality import QualityInspector
from patangoma.services.sample_generator import create_minimal_flac, create_minimal_mp3


def test_quality_inspector_mp3(tmp_path: Path) -> None:
    f = create_minimal_mp3(
        tmp_path / "track.mp3", {"title": "MP3 Track", "artist": "Singer"}
    )
    qi = QualityInspector()
    rep = qi.inspect_file(f)

    assert rep.format == "mp3"
    assert rep.quality_grade in ("HIGH_BITRATE", "MEDIUM_BITRATE", "LOW_BITRATE")


def test_quality_inspector_flac(tmp_path: Path) -> None:
    f = create_minimal_flac(
        tmp_path / "track.flac", {"title": "FLAC Track", "artist": "Singer"}
    )
    qi = QualityInspector()
    rep = qi.inspect_file(f)

    assert rep.format == "flac"
    assert rep.quality_grade in ("LOSSLESS", "SUSPICIOUS")
