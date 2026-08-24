"""Sample audio library and synthetic audio file generator."""

from __future__ import annotations

import struct
import wave
from pathlib import Path
from typing import Any

from mediafile import MediaFile


def create_minimal_wav(path: str | Path, tags: dict[str, Any] | None = None) -> Path:
    """Create a minimal valid silent WAV file and optionally apply tags."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)

    with wave.open(str(p), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(44100)
        w.writeframes(b"\x00" * 4410)  # 0.1s silence

    if tags:
        mf = MediaFile(str(p))
        for key, val in tags.items():
            if hasattr(mf, key):
                setattr(mf, key, val)
        mf.save()

    return p


def create_minimal_mp3(path: str | Path, tags: dict[str, Any] | None = None) -> Path:
    """Create a minimal valid silent MP3 file and optionally apply tags."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)

    # 10 frames of MPEG-1 Layer 3, 128kbps, 44.1kHz stereo silence
    mp3_frame = b"\xff\xfb\x90\x64" + (b"\x00" * 413)
    p.write_bytes(mp3_frame * 10)

    if tags:
        mf = MediaFile(str(p))
        for key, val in tags.items():
            if hasattr(mf, key):
                setattr(mf, key, val)
        mf.save()

    return p


def create_minimal_flac(path: str | Path, tags: dict[str, Any] | None = None) -> Path:
    """Create a minimal valid silent FLAC file and optionally apply tags."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)

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
    p.write_bytes(flac_bytes)

    if tags:
        mf = MediaFile(str(p))
        for key, val in tags.items():
            if hasattr(mf, key):
                setattr(mf, key, val)
        mf.save()

    return p


def create_corrupt_file(path: str | Path) -> Path:
    """Create a corrupt file with non-audio garbage bytes."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(b"\xde\xad\xbe\xef\x00\x11\x22\x33\x44\x55\x66\x77\x88\x99")
    return p


def generate_sample_library(output_dir: str | Path) -> dict[str, list[str]]:
    """Generate a realistic test music library with valid, partial, and edge-case audio files."""
    base = Path(output_dir)
    base.mkdir(parents=True, exist_ok=True)

    created_files: dict[str, list[str]] = {
        "complete": [],
        "missing_metadata": [],
        "unicode": [],
        "corrupt": [],
    }

    # 1. Complete MP3
    f1 = base / "01 - Burna Boy - Last Last.mp3"
    create_minimal_mp3(
        f1,
        {
            "title": "Last Last",
            "artist": "Burna Boy",
            "album": "Love, Damini",
            "albumartist": "Burna Boy",
            "year": 2022,
            "track": 1,
            "tracktotal": 19,
            "genre": "Afrobeats",
        },
    )
    created_files["complete"].append(str(f1))

    # 2. Complete FLAC
    f2 = base / "02 - Sauti Sol - Suzanna.flac"
    create_minimal_flac(
        f2,
        {
            "title": "Suzanna",
            "artist": "Sauti Sol",
            "album": "Midnight Train",
            "albumartist": "Sauti Sol",
            "year": 2020,
            "track": 2,
            "tracktotal": 13,
            "genre": "Afro-Pop",
        },
    )
    created_files["complete"].append(str(f2))

    # 3. Complete WAV
    f3 = base / "03 - Ayra Starr - Rush.wav"
    create_minimal_wav(
        f3,
        {
            "title": "Rush",
            "artist": "Ayra Starr",
            "album": "19 & Dangerous (Deluxe)",
            "year": 2022,
            "track": 3,
            "tracktotal": 16,
            "genre": "Afrobeats",
        },
    )
    created_files["complete"].append(str(f3))

    # 4. Missing Artist (Only Title in Tags)
    f4 = base / "04 - Calm Down.mp3"
    create_minimal_mp3(f4, {"title": "Calm Down"})
    created_files["missing_metadata"].append(str(f4))

    # 5. Untagged Audio File with clean filename pattern
    f5 = base / "05 - Rema - Holiday.mp3"
    create_minimal_mp3(f5, {})
    created_files["missing_metadata"].append(str(f5))

    # 6. Multilingual / Unicode Tags
    f6 = base / "06 - Miriam Makeba - Malaika (天使).flac"
    create_minimal_flac(
        f6,
        {
            "title": "Malaika (天使)",
            "artist": "Miriam Makeba",
            "album": "African Classics",
            "year": 1965,
            "genre": "World / Folk",
        },
    )
    created_files["unicode"].append(str(f6))

    # 7. Corrupt audio file for diagnostic testing
    f7 = base / "07 - Corrupt Stream.mp3"
    create_corrupt_file(f7)
    created_files["corrupt"].append(str(f7))

    return created_files
