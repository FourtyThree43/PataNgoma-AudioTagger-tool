"""Unit tests for enhanced rollback features (rollback_latest and rollback_path)."""

from __future__ import annotations

from pathlib import Path

from patangoma.domain.models import (
    ConfidenceLevel,
    FieldDiffStatus,
    TagFieldDiff,
    TagPlan,
)
from patangoma.services.audio_backend import AudioBackend, compute_file_checksum
from patangoma.services.audit import AuditJournal


def test_rollback_latest_and_path(
    mp3_complete: Path, flac_complete: Path, tmp_path: Path
):
    db_file = tmp_path / "rollback_test.db"
    journal = AuditJournal(db_path=db_file)
    backend = AudioBackend()

    # Track 1 mutation
    before_1 = backend.read_metadata(mp3_complete)
    plan_1 = TagPlan(
        file_path=str(mp3_complete),
        provider_name="itunes",
        provider_id="itunes-1",
        confidence=ConfidenceLevel.EXACT,
        total_score=1.0,
        checksum_pre=compute_file_checksum(mp3_complete),
        diffs=[
            TagFieldDiff(
                field_name="title",
                old_value=before_1.title,
                new_value="New Title 1",
                status=FieldDiffStatus.MODIFIED,
            )
        ],
    )
    after_1 = backend.write_tags(mp3_complete, {"title": "New Title 1"})
    journal.record_apply(plan_1, before_1, after_1)

    # Track 2 mutation
    before_2 = backend.read_metadata(flac_complete)
    plan_2 = TagPlan(
        file_path=str(flac_complete),
        provider_name="discogs",
        provider_id="discogs-2",
        confidence=ConfidenceLevel.EXACT,
        total_score=1.0,
        checksum_pre=compute_file_checksum(flac_complete),
        diffs=[
            TagFieldDiff(
                field_name="title",
                old_value=before_2.title,
                new_value="New Title 2",
                status=FieldDiffStatus.MODIFIED,
            )
        ],
    )
    after_2 = backend.write_tags(flac_complete, {"title": "New Title 2"})
    journal.record_apply(plan_2, before_2, after_2)

    # Test rollback_latest (reverts Track 2)
    restored_latest = journal.rollback_latest(backend)
    assert restored_latest.title == before_2.title

    # Test rollback_path on Track 1
    restored_path = journal.rollback_path(mp3_complete, backend)
    assert len(restored_path) == 1
    assert restored_path[0].title == before_1.title
