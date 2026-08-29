"""Audio metadata extraction and mutation backend (re-exports from infrastructure.media)."""

from __future__ import annotations

from patangoma.infrastructure.media.backend import (
    AudioBackendPort,
    MediaFileAudioBackend,
    compute_file_checksum,
)

# Backward-compatible alias for existing service consumers
AudioBackend = MediaFileAudioBackend

__all__ = [
    "AudioBackend",
    "AudioBackendPort",
    "MediaFileAudioBackend",
    "compute_file_checksum",
]
