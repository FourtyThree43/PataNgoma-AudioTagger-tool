"""Synthetic audio file generator for testing PataNgoma without proprietary media."""

from __future__ import annotations

import struct
import wave
from pathlib import Path
from typing import Any

from mediafile import MediaFile


def create_minimal_wav(path: str | Path, tags: dict[str, Any] | None = None) -> Path:
    """Create a minimal valid silent WAV file and optionally apply tags."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(44100)
        w.writeframes(b"\x00" * 4410)  # 0.1s silence

    if tags:
        mf = MediaFile(str(path))
        for key, val in tags.items():
            if hasattr(mf, key):
                setattr(mf, key, val)
        mf.save()

    return path


def create_minimal_mp3(path: str | Path, tags: dict[str, Any] | None = None) -> Path:
    """Create a minimal valid silent MP3 file and optionally apply tags."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    # 10 frames of MPEG-1 Layer 3, 128kbps, 44.1kHz stereo silence
    mp3_frame = b"\xff\xfb\x90\x64" + (b"\x00" * 413)
    path.write_bytes(mp3_frame * 10)

    if tags:
        mf = MediaFile(str(path))
        for key, val in tags.items():
            if hasattr(mf, key):
                setattr(mf, key, val)
        mf.save()

    return path


def create_minimal_flac(path: str | Path, tags: dict[str, Any] | None = None) -> Path:
    """Create a minimal valid silent FLAC file and optionally apply tags."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    min_block = 4096
    max_block = 4096
    min_frame = 0
    max_frame = 0
    sample_rate = 44100
    channels = 2
    bps = 16
    total_samples = 44100
    md5 = b"\x00" * 16

    sr_chan_bps_samples = (
        (sample_rate << 44) | ((channels - 1) << 41) | ((bps - 1) << 36) | total_samples
    )

    streaminfo = struct.pack(
        ">HH3s3s8s16s",
        min_block,
        max_block,
        min_frame.to_bytes(3, "big"),
        max_frame.to_bytes(3, "big"),
        sr_chan_bps_samples.to_bytes(8, "big"),
        md5,
    )

    flac_bytes = b"fLaC\x80\x00\x00\x22" + streaminfo
    path.write_bytes(flac_bytes)

    if tags:
        mf = MediaFile(str(path))
        for key, val in tags.items():
            if hasattr(mf, key):
                setattr(mf, key, val)
        mf.save()

    return path


def create_corrupt_file(path: str | Path) -> Path:
    """Create a corrupt file with non-audio garbage bytes."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"\xde\xad\xbe\xef\x00\x11\x22\x33\x44\x55\x66\x77\x88\x99")
    return path


def create_audio_fixture(
    fmt: str,
    temp_dir: str | Path,
    filename: str,
    tags: dict[str, Any] | None = None,
) -> Path:
    """Create an audio fixture of specified format in a temporary directory."""
    full_path = Path(temp_dir) / f"{filename}.{fmt}"
    if fmt == "mp3":
        return create_minimal_mp3(full_path, tags)
    elif fmt == "flac":
        return create_minimal_flac(full_path, tags)
    elif fmt == "wav":
        return create_minimal_wav(full_path, tags)
    elif fmt == "corrupt":
        return create_corrupt_file(full_path)
    else:
        raise ValueError(f"Unsupported format for synthetic fixture: {fmt}")
