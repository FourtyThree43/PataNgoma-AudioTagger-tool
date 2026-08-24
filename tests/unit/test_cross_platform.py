"""Unit tests for cross-platform path handling, Windows-style paths, and unicode filesystem paths."""

from __future__ import annotations

from pathlib import Path

from patangoma.domain.models import (
    ConfidenceLevel,
    FieldDiffStatus,
    TagFieldDiff,
    TagPlan,
    TrackMetadata,
)
from patangoma.services.audio_backend import AudioBackend
from patangoma.services.audit import AuditJournal
from patangoma.services.scanner import LibraryScanner


def test_windows_and_posix_path_models():
    # Windows absolute path
    win_path = "C:\\Music\\Afrobeats\\Burna Boy - Last Last.mp3"
    meta_win = TrackMetadata(
        file_path=win_path,
        file_format="mp3",
        title="Last Last",
        artist="Burna Boy",
    )
    assert meta_win.file_path == win_path
    assert meta_win.path.name == "Burna Boy - Last Last.mp3"

    # Plan serialization with Windows path
    plan = TagPlan(
        file_path=win_path,
        provider_name="spotify",
        provider_id="spot-99",
        confidence=ConfidenceLevel.EXACT,
        total_score=0.98,
        checksum_pre="abc123sha256",
        diffs=[
            TagFieldDiff(
                field_name="title",
                old_value="Last Last",
                new_value="Last Last (Remix)",
                status=FieldDiffStatus.MODIFIED,
            )
        ],
    )
    dumped = plan.model_dump(mode="json")
    assert dumped["file_path"] == win_path

    restored = TagPlan.model_validate(dumped)
    assert restored.file_path == win_path


def test_unicode_and_special_character_paths(tmp_path: Path, complete_tags: dict):
    # Test path with spaces, parentheses, accents, non-ASCII characters
    special_name = "01. Malaika (天使) — 特别版.mp3"
    special_file = tmp_path / special_name

    from tests.helpers.audio_factory import create_minimal_mp3

    create_minimal_mp3(special_file, complete_tags)

    backend = AudioBackend()
    meta = backend.read_metadata(special_file)
    assert meta.title == complete_tags["title"]
    assert meta.path.exists()

    # Scanner discovers unicode file path
    scanner = LibraryScanner(backend)
    tracks, summary = scanner.scan_directory(tmp_path)
    assert summary.valid_audio_files == 1
    assert tracks[0].title == complete_tags["title"]


def test_audit_journal_cross_platform_paths(tmp_path: Path, mp3_complete: Path):
    db_file = tmp_path / "cross_platform_audit.db"
    journal = AuditJournal(db_path=db_file)

    plan = TagPlan(
        file_path=str(mp3_complete),
        provider_name="musicbrainz",
        provider_id="mb-win-1",
        confidence=ConfidenceLevel.EXACT,
        total_score=1.0,
        checksum_pre="hashpre123",
        diffs=[],
    )

    track_before = TrackMetadata(
        file_path=str(mp3_complete), title="Old Title", artist="Old Artist"
    )
    track_after = TrackMetadata(
        file_path=str(mp3_complete), title="New Title", artist="New Artist"
    )

    rec = journal.record_apply(plan, track_before, track_after)
    assert rec.file_path == str(mp3_complete)

    history = journal.list_history()
    assert len(history) == 1
    assert history[0].file_path == str(mp3_complete)
