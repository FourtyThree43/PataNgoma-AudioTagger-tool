"""Unit tests for AuditJournal and rollback service."""

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


def test_audit_journal_record_and_rollback(mp3_complete: Path, tmp_path: Path):
    db_file = tmp_path / "test_audit.db"
    journal = AuditJournal(db_path=db_file)
    backend = AudioBackend()

    # Initial state
    track_before = backend.read_metadata(mp3_complete)
    original_title = track_before.title
    original_artist = track_before.artist
    checksum_pre = compute_file_checksum(mp3_complete)

    # Create and apply plan
    plan = TagPlan(
        file_path=str(mp3_complete),
        provider_name="spotify",
        provider_id="spot-1",
        confidence=ConfidenceLevel.EXACT,
        total_score=0.99,
        checksum_pre=checksum_pre,
        diffs=[
            TagFieldDiff(
                field_name="title",
                old_value=original_title,
                new_value="Brand New Title",
                status=FieldDiffStatus.MODIFIED,
            ),
            TagFieldDiff(
                field_name="artist",
                old_value=original_artist,
                new_value="Brand New Artist",
                status=FieldDiffStatus.MODIFIED,
            ),
        ],
    )

    track_after = backend.write_tags(
        mp3_complete, {"title": "Brand New Title", "artist": "Brand New Artist"}
    )
    audit_rec = journal.record_apply(plan, track_before, track_after)

    # Verify history
    history = journal.list_history()
    assert len(history) == 1
    assert history[0].operation_id == audit_rec.operation_id
    assert history[0].file_path == str(mp3_complete)

    # Mutated file check
    mutated = backend.read_metadata(mp3_complete)
    assert mutated.title == "Brand New Title"
    assert mutated.artist == "Brand New Artist"

    # Execute rollback
    restored = journal.rollback_operation(audit_rec.operation_id, backend)
    assert restored.title == original_title
    assert restored.artist == original_artist

    # Confirm disk state
    disk_verified = backend.read_metadata(mp3_complete)
    assert disk_verified.title == original_title
    assert disk_verified.artist == original_artist
