"""Unit tests for PlanEngine service."""

from __future__ import annotations

from pathlib import Path

from patangoma.domain.models import (
    ConfidenceLevel,
    FieldDiffStatus,
    MetadataCandidate,
    TrackMetadata,
)
from patangoma.services.planner import PlanEngine


def test_plan_engine_create_plan(mp3_missing_artist: Path):
    engine = PlanEngine()
    track = TrackMetadata(
        file_path=str(mp3_missing_artist),
        title="Mystery Track",
        artist=None,
        album="Old Album",
    )
    candidate = MetadataCandidate(
        provider_name="musicbrainz",
        provider_id="rec-99",
        title="Mystery Track",
        artists=["Discovered Artist"],
        album="New Deluxe Album",
        year=2021,
    )

    plan = engine.create_plan(
        track=track,
        candidate=candidate,
        confidence=ConfidenceLevel.HIGH,
        total_score=0.88,
    )

    assert plan.file_path == str(mp3_missing_artist)
    assert plan.provider_name == "musicbrainz"
    assert plan.has_changes is True

    # Check specific field diffs
    diff_map = {d.field_name: d for d in plan.diffs}

    assert diff_map["title"].status == FieldDiffStatus.UNCHANGED
    assert diff_map["artist"].status == FieldDiffStatus.ADDED
    assert diff_map["artist"].new_value == "Discovered Artist"
    assert diff_map["album"].status == FieldDiffStatus.MODIFIED
    assert diff_map["album"].old_value == "Old Album"
    assert diff_map["album"].new_value == "New Deluxe Album"


def test_plan_engine_json_roundtrip(mp3_complete: Path, tmp_path: Path):
    engine = PlanEngine()
    track = TrackMetadata(
        file_path=str(mp3_complete),
        title="Original",
        artist="Original",
    )
    candidate = MetadataCandidate(
        provider_name="deezer",
        provider_id="dz-1",
        title="Updated",
        artists=["Updated"],
    )

    plan = engine.create_plan(
        track=track,
        candidate=candidate,
        confidence=ConfidenceLevel.EXACT,
        total_score=0.98,
    )

    plan_file = tmp_path / "test_plan.json"
    engine.save_plan_file(plan, plan_file)

    loaded_plan = engine.load_plan_from_json(plan_file.read_text(encoding="utf-8"))
    assert loaded_plan.file_path == plan.file_path
    assert loaded_plan.provider_id == "dz-1"
    assert loaded_plan.confidence == ConfidenceLevel.EXACT
    assert len(loaded_plan.diffs) == len(plan.diffs)
