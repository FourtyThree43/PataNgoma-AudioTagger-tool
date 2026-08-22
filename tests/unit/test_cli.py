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
