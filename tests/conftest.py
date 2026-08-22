"""Pytest configuration and shared fixtures for PataNgoma."""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.helpers.audio_factory import (
    create_corrupt_file,
    create_minimal_flac,
    create_minimal_mp3,
    create_minimal_wav,
)


@pytest.fixture
def complete_tags() -> dict:
    """Fixture containing a complete set of valid track tags."""
    return {
        "title": "Sauti ya Simba",
        "artist": "Burna Boy",
        "album": "Love, Damini",
        "albumartist": "Burna Boy",
        "genre": "Afrobeats",
        "year": 2022,
        "track": 3,
        "tracktotal": 19,
        "disc": 1,
        "disctotal": 1,
        "composer": "Damini Ogulu",
    }


@pytest.fixture
def unicode_tags() -> dict:
    """Fixture containing unicode/multilingual metadata tags."""
    return {
        "title": "Malaika (天使) — 🎵 Special Remaster",
        "artist": "Fadhili William & Miriam Makeba",
        "album": "African Classics / Hakuna Matata",
        "genre": "World / Folk",
        "year": 1963,
    }


@pytest.fixture
def mp3_complete(tmp_path: Path, complete_tags: dict) -> Path:
    """A valid MP3 file with complete metadata."""
    return create_minimal_mp3(tmp_path / "complete.mp3", complete_tags)


@pytest.fixture
def mp3_missing_title(tmp_path: Path) -> Path:
    """An MP3 file with artist but missing title."""
    return create_minimal_mp3(
        tmp_path / "missing_title.mp3", {"artist": "Unknown Artist"}
    )


@pytest.fixture
def mp3_missing_artist(tmp_path: Path) -> Path:
    """An MP3 file with title but missing artist."""
    return create_minimal_mp3(
        tmp_path / "missing_artist.mp3", {"title": "Mystery Track"}
    )


@pytest.fixture
def mp3_empty(tmp_path: Path) -> Path:
    """An MP3 file with no tag metadata."""
    return create_minimal_mp3(tmp_path / "empty.mp3", {})


@pytest.fixture
def flac_complete(tmp_path: Path, complete_tags: dict) -> Path:
    """A valid FLAC file with complete metadata."""
    return create_minimal_flac(tmp_path / "complete.flac", complete_tags)


@pytest.fixture
def wav_complete(tmp_path: Path, complete_tags: dict) -> Path:
    """A valid WAV file with complete metadata."""
    return create_minimal_wav(tmp_path / "complete.wav", complete_tags)


@pytest.fixture
def corrupt_audio_file(tmp_path: Path) -> Path:
    """A non-audio corrupt file."""
    return create_corrupt_file(tmp_path / "corrupted.mp3")
