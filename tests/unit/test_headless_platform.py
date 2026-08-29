"""Headless Platform Acceptance Test (Specification Section 47)."""

from __future__ import annotations

from pathlib import Path

from patangoma.bootstrap.application import create_application
from patangoma.domain.models import MetadataCandidate
from tests.helpers.audio_factory import create_minimal_mp3


def test_headless_platform_workflow(tmp_path: Path):
    """Verify major workflows execute headlessly in pure Python without UI dependencies."""
    # Create synthetic test audio
    audio_path = tmp_path / "song.mp3"
    create_minimal_mp3(
        audio_path,
        {
            "title": "Before Tag",
            "artist": "Old Artist",
            "album": "Old Album",
            "year": 2020,
        },
    )

    db_path = tmp_path / "test_audit.db"
    app = create_application(audit_db_path=db_path)

    # 1. Scan Library
    tracks, summary = app.scan_library(tmp_path, recursive=False)
    assert summary.valid_audio_files == 1
    assert len(tracks) == 1
    assert tracks[0].title == "Before Tag"

    # 2. Inspect Metadata
    meta = app.read_metadata(audio_path)
    assert meta.artist == "Old Artist"

    # 3. Create Tag Plan with Candidate
    cand = MetadataCandidate(
        provider_name="musicbrainz",
        provider_id="mb-test-1",
        title="Enhanced Title",
        artists=["New Artist"],
        album="New Album",
        year=2024,
    )
    plan = app.create_tag_plan(audio_path, cand)
    assert plan.has_changes is True
    assert plan.provider_name == "musicbrainz"

    # 4. Apply Tag Plan
    updated = app.apply_tag_plan(plan, dry_run=False)
    assert updated.title == "Enhanced Title"
    assert updated.artist == "New Artist"
    assert updated.album == "New Album"

    # Verify on-disk re-read
    verified = app.read_metadata(audio_path)
    assert verified.title == "Enhanced Title"

    # 5. Check Audit Journal History
    history = app.get_audit_history(file_path=str(audio_path.resolve()))
    assert len(history) >= 1
    assert history[0].backup_tags["title"] == "Before Tag"

    # 6. Rollback Operation
    rolled_back = app.rollback(file_path=str(audio_path.resolve()))
    assert rolled_back.title == "Before Tag"
    assert rolled_back.artist == "Old Artist"

    # Verify on-disk rollback
    final_meta = app.read_metadata(audio_path)
    assert final_meta.title == "Before Tag"
