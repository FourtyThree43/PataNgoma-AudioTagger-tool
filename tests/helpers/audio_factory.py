"""Synthetic audio file generator helpers for tests (re-exports from services.sample_generator)."""

from __future__ import annotations

from patangoma.services.sample_generator import (
    create_corrupt_file,
    create_minimal_flac,
    create_minimal_mp3,
    create_minimal_wav,
    generate_sample_library,
)

__all__ = [
    "create_corrupt_file",
    "create_minimal_flac",
    "create_minimal_mp3",
    "create_minimal_wav",
    "generate_sample_library",
]
