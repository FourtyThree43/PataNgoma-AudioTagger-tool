"""Comprehensive CLI tests using Click's CliRunner."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

from patangoma.cli import cli
from patangoma.domain.models import MetadataCandidate


def test_cli_doctor():
    runner = CliRunner()
    result = runner.invoke(cli, ["doctor"])
    assert result.exit_code == 0
    assert "Python Runtime" in result.output
    assert "Audio Metadata Backend" in result.output

    # Test JSON output
    json_res = runner.invoke(cli, ["doctor", "--json"])
    assert json_res.exit_code == 0
    parsed = json.loads(json_res.output)
    assert "overall_healthy" in parsed
    assert "checks" in parsed


def test_cli_inspect(mp3_complete: Path, complete_tags: dict):
    runner = CliRunner()
    result = runner.invoke(cli, ["inspect", str(mp3_complete)])
    assert result.exit_code == 0
    assert complete_tags["title"] in result.output
    assert complete_tags["artist"] in result.output

    # JSON inspect
    json_res = runner.invoke(cli, ["inspect", str(mp3_complete), "--json"])
    assert json_res.exit_code == 0
    parsed = json.loads(json_res.output)
    assert parsed["title"] == complete_tags["title"]
    assert parsed["artist"] == complete_tags["artist"]


def test_cli_scan(tmp_path: Path, mp3_complete: Path):
    runner = CliRunner()
    result = runner.invoke(cli, ["scan", str(mp3_complete.parent)])
    assert result.exit_code == 0
    assert "Library Scan Summary" in result.output

    # JSON scan
    json_res = runner.invoke(cli, ["scan", str(mp3_complete.parent), "--json"])
    assert json_res.exit_code == 0
    parsed = json.loads(json_res.output)
    assert parsed["total_files_scanned"] >= 1
    assert parsed["valid_audio_files"] >= 1


def test_cli_verify(tmp_path: Path, mp3_complete: Path):
    runner = CliRunner()
    result = runner.invoke(cli, ["verify", str(mp3_complete.parent)])
    assert result.exit_code == 0
    assert "verified successfully" in result.output

    # JSON verify
    json_res = runner.invoke(cli, ["verify", str(mp3_complete.parent), "--json"])
    assert json_res.exit_code == 0
    parsed = json.loads(json_res.output)
    assert parsed["total_files"] >= 1
    assert parsed["verified_readable"] >= 1


def test_cli_plan_and_apply_mocked(mp3_missing_artist: Path, tmp_path: Path):
    runner = CliRunner()
    mock_candidate = MetadataCandidate(
        provider_name="musicbrainz",
        provider_id="rec-42",
        title="Mystery Track",
        artists=["Resolved Artist"],
        album="Resolved Album",
        year=2024,
    )

    with patch(
        "patangoma.providers.musicbrainz.MusicBrainzProvider.search_tracks",
        return_value=[mock_candidate],
    ):
        plan_file = tmp_path / "plan.json"

        # 1. Generate plan
        plan_res = runner.invoke(
            cli, ["plan", str(mp3_missing_artist), "-o", str(plan_file)]
        )
        assert plan_res.exit_code == 0
        assert plan_file.exists()

        # 2. Dry run apply
        dry_res = runner.invoke(cli, ["apply", str(plan_file), "--dry-run"])
        assert dry_res.exit_code == 0
        assert "DRY-RUN" in dry_res.output

        # 3. Real apply
        apply_res = runner.invoke(cli, ["apply", str(plan_file)])
        assert apply_res.exit_code == 0
        assert "Successfully applied plan" in apply_res.output

        # 4. Check history
        hist_res = runner.invoke(cli, ["history"])
        assert hist_res.exit_code == 0
        assert "Audit Log & Mutation History" in hist_res.output


def test_cli_plan_dir_and_apply_dir_mocked(mp3_complete: Path, tmp_path: Path):
    runner = CliRunner()
    mock_candidate = MetadataCandidate(
        provider_name="musicbrainz",
        provider_id="rec-99",
        title="Sauti ya Simba",
        artists=["Burna Boy"],
        album="Love, Damini (Deluxe)",
        year=2022,
    )

    with patch(
        "patangoma.providers.musicbrainz.MusicBrainzProvider.search_tracks",
        return_value=[mock_candidate],
    ):
        batch_file = tmp_path / "batch.json"

        # 1. Generate batch plan
        plan_res = runner.invoke(
            cli, ["plan-dir", str(mp3_complete.parent), "-o", str(batch_file)]
        )
        assert plan_res.exit_code == 0
        assert batch_file.exists()

        # 2. Dry run apply batch
        dry_res = runner.invoke(cli, ["apply-dir", str(batch_file), "--dry-run"])
        assert dry_res.exit_code == 0
        assert "DRY-RUN" in dry_res.output

        # 3. Real apply batch
        apply_res = runner.invoke(cli, ["apply-dir", str(batch_file)])
        assert apply_res.exit_code == 0
        assert "Successfully applied batch plan" in apply_res.output


def test_cli_reason(mp3_complete: Path):
    runner = CliRunner()
    result = runner.invoke(cli, ["reason", str(mp3_complete)])
    assert result.exit_code == 0
    assert "Filename & Tag Reasoning" in result.output

    # JSON test
    json_res = runner.invoke(cli, ["reason", str(mp3_complete), "--json"])
    assert json_res.exit_code == 0
    parsed = json.loads(json_res.output)
    assert "inference" in parsed
    assert "suggestions" in parsed


def test_cli_match_untagged_file_heuristic(tmp_path: Path):
    from patangoma.services.sample_generator import create_minimal_mp3

    # Generate untagged file "09 - LUMINOUS.mp3"
    untagged_file = tmp_path / "09 - LUMINOUS.mp3"
    create_minimal_mp3(untagged_file, tags={})

    runner = CliRunner()
    mock_candidate = MetadataCandidate(
        provider_name="itunes",
        provider_id="itunes-123",
        title="LUMINOUS",
        artists=["Aina The End"],
        album="Luminous - Single",
    )

    with patch(
        "patangoma.providers.itunes.ITunesProvider.search_tracks",
        return_value=[mock_candidate],
    ):
        res = runner.invoke(cli, ["match", str(untagged_file), "--provider", "itunes"])
        assert res.exit_code == 0
        assert "Inferred title 'LUMINOUS'" in res.output
        assert "LUMINOUS" in res.output


def test_cli_match_multi_provider(tmp_path: Path):
    from patangoma.services.sample_generator import create_minimal_mp3

    track_file = tmp_path / "test.mp3"
    create_minimal_mp3(track_file, tags={"title": "Test Song", "artist": "Test Artist"})

    runner = CliRunner()
    mock_candidate = MetadataCandidate(
        provider_name="itunes",
        provider_id="itunes-456",
        title="Test Song",
        artists=["Test Artist"],
        album="Test Album",
    )

    with patch(
        "patangoma.services.aggregator.MetadataAggregator.search_all_providers",
        return_value=[mock_candidate],
    ):
        res = runner.invoke(cli, ["match", str(track_file), "--provider", "multi"])
        assert res.exit_code == 0
        assert "Test Song" in res.output


def test_cli_tag_command(tmp_path: Path):
    from patangoma.services.sample_generator import create_minimal_mp3

    track_file = tmp_path / "test.mp3"
    create_minimal_mp3(track_file, tags={"title": "Old Title", "artist": "Old Artist"})

    runner = CliRunner()
    mock_candidate = MetadataCandidate(
        provider_name="itunes",
        provider_id="itunes-789",
        title="New Title",
        artists=["New Artist"],
        album="New Album",
    )

    with patch(
        "patangoma.providers.itunes.ITunesProvider.search_tracks",
        return_value=[mock_candidate],
    ):
        res = runner.invoke(
            cli, ["tag", str(track_file), "--provider", "itunes", "--no-interactive"]
        )
        assert res.exit_code == 0
        assert "Successfully applied tags" in res.output


def test_cli_replaygain_command(tmp_path: Path):
    from patangoma.services.sample_generator import create_minimal_mp3

    track_file = tmp_path / "test.mp3"
    create_minimal_mp3(track_file, tags={"title": "Song", "artist": "Artist"})

    runner = CliRunner()
    res = runner.invoke(cli, ["replaygain", str(track_file)])
    assert res.exit_code == 0
    assert "Applied ReplayGain tags" in res.output


def test_cli_normalize_genres_command(tmp_path: Path):
    from patangoma.services.sample_generator import create_minimal_mp3

    track_file = tmp_path / "test.mp3"
    create_minimal_mp3(
        track_file, tags={"title": "Song", "artist": "Artist", "genre": "hip hop"}
    )

    runner = CliRunner()
    res = runner.invoke(cli, ["normalize-genres", str(track_file)])
    assert res.exit_code == 0
    assert "Normalized 1 genre tags" in res.output


def test_cli_playlist_export_and_cue_inspect(tmp_path: Path):
    from patangoma.services.sample_generator import create_minimal_mp3

    track_file = tmp_path / "test.mp3"
    create_minimal_mp3(track_file, tags={"title": "Song", "artist": "Artist"})

    runner = CliRunner()
    m3u_out = tmp_path / "out.m3u8"
    res = runner.invoke(cli, ["playlist-export", str(tmp_path), "-o", str(m3u_out)])
    assert res.exit_code == 0
    assert m3u_out.exists()

    cue_file = tmp_path / "sheet.cue"
    cue_file.write_text('TRACK 01 AUDIO\nTITLE "Test Cue"', encoding="utf-8")
    res_cue = runner.invoke(cli, ["cue-inspect", str(cue_file)])
    assert res_cue.exit_code == 0
    assert "Test Cue" in res_cue.output


def test_cli_export_catalog_and_transcode_check(tmp_path: Path):
    from patangoma.services.sample_generator import create_minimal_mp3

    track_file = tmp_path / "test.mp3"
    create_minimal_mp3(track_file, tags={"title": "Song", "artist": "Artist"})

    runner = CliRunner()
    cat_out = tmp_path / "catalog.json"
    res_cat = runner.invoke(cli, ["export-catalog", str(tmp_path), "-o", str(cat_out)])
    assert res_cat.exit_code == 0
    assert cat_out.exists()

    res_tc = runner.invoke(cli, ["transcode-check", str(track_file)])
    assert res_tc.exit_code == 0
    assert "MP3" in res_tc.output
