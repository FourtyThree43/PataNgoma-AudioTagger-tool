"""Sample audio library generator for testing, demonstrations, and development."""

from __future__ import annotations

from pathlib import Path

from tests.helpers.audio_factory import (
    create_corrupt_file,
    create_minimal_flac,
    create_minimal_mp3,
    create_minimal_wav,
)


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
