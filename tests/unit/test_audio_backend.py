"""Unit tests for AudioBackend service."""

from __future__ import annotations

from pathlib import Path

import pytest

from patangoma.domain.exceptions import (
    AudioFileNotFoundError,
    CorruptAudioFileError,
    InvalidAudioFileError,
)
from patangoma.services.audio_backend import AudioBackend, compute_file_checksum


def test_audio_backend_read_complete(mp3_complete: Path, complete_tags: dict):
    backend = AudioBackend()
    meta = backend.read_metadata(mp3_complete)

    assert meta.title == complete_tags["title"]
    assert meta.artist == complete_tags["artist"]
    assert meta.album == complete_tags["album"]
    assert meta.year == complete_tags["year"]
    assert meta.file_format == "mp3"


def test_audio_backend_write_and_dry_run(mp3_empty: Path):
    backend = AudioBackend()

    # Dry-run write
    dry_meta = backend.write_tags(mp3_empty, {"title": "Simulated Title"}, dry_run=True)
    assert dry_meta.title == "Simulated Title"

    # Verify disk was not mutated
    real_meta = backend.read_metadata(mp3_empty)
    assert real_meta.title is None

    # Real write
    written_meta = backend.write_tags(
        mp3_empty, {"title": "Actual Title", "artist": "Actual Artist"}
    )
    assert written_meta.title == "Actual Title"
    assert written_meta.artist == "Actual Artist"

    # Verify on disk
    reloaded = backend.read_metadata(mp3_empty)
    assert reloaded.title == "Actual Title"
    assert reloaded.artist == "Actual Artist"


def test_audio_backend_nonexistent_file(tmp_path: Path):
    backend = AudioBackend()
    with pytest.raises(AudioFileNotFoundError):
        backend.read_metadata(tmp_path / "nonexistent.mp3")


def test_audio_backend_corrupt_file(corrupt_audio_file: Path):
    backend = AudioBackend()
    with pytest.raises((InvalidAudioFileError, CorruptAudioFileError)):
        backend.read_metadata(corrupt_audio_file)


def test_compute_file_checksum(mp3_complete: Path):
    checksum1 = compute_file_checksum(mp3_complete)
    assert isinstance(checksum1, str)
    assert len(checksum1) == 64  # SHA-256 hex string

    checksum2 = compute_file_checksum(mp3_complete)
    assert checksum1 == checksum2
