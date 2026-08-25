"""Unit tests for ReplayGain and loudness scanning service."""

from pathlib import Path

from patangoma.services.replaygain import ReplayGainService
from patangoma.services.sample_generator import create_minimal_mp3


def test_replaygain_calculation_and_tagging(tmp_path: Path) -> None:
    f = create_minimal_mp3(tmp_path / "test.mp3", {"title": "Test", "artist": "Singer"})
    rg = ReplayGainService()

    result = rg.calculate_track_gain(f)
    assert result.track_gain_db is not None
    assert 0.0 <= result.track_peak <= 1.0

    tags = rg.apply_replaygain_tags(f, result, dry_run=False)
    assert "replaygain_track_gain" in tags
    assert "replaygain_track_peak" in tags
