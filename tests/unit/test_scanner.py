"""Unit tests for LibraryScanner service."""

from __future__ import annotations

from pathlib import Path

from patangoma.services.scanner import LibraryScanner
from tests.helpers.audio_factory import (
    create_corrupt_file,
    create_minimal_flac,
    create_minimal_mp3,
)


def test_library_scanner_scan_directory(tmp_path: Path):
    music_dir = tmp_path / "music"
    music_dir.mkdir()

    # 1. Complete MP3
    create_minimal_mp3(
        music_dir / "complete.mp3",
        {"title": "Song 1", "artist": "Artist 1", "album": "Album 1", "year": 2020},
    )

    # 2. Missing title MP3
    create_minimal_mp3(
        music_dir / "no_title.mp3",
        {"artist": "Artist 2", "album": "Album 2"},
    )

    # 3. Complete FLAC
    create_minimal_flac(
        music_dir / "track.flac",
        {"title": "Song 1", "artist": "Artist 1", "album": "Album 1", "year": 2020},
    )

    # 4. Corrupt file with audio extension
    create_corrupt_file(music_dir / "broken.mp3")

    scanner = LibraryScanner()
    _tracks, summary = scanner.scan_directory(music_dir)

    assert summary.total_files_scanned == 4
    assert summary.valid_audio_files == 3
    assert summary.corrupt_or_unreadable == 1
    assert summary.missing_title_count == 1
    assert len(summary.errors) == 1

    # Duplicate detection: "Song 1" by "Artist 1" in both MP3 and FLAC
    assert len(summary.duplicate_groups) == 1
    assert len(summary.duplicate_groups[0]) == 2
