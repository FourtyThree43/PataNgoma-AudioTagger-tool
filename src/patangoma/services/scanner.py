"""Recursive audio library scanner and health inspector."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from pydantic import BaseModel, Field

from patangoma.domain.exceptions import AudioFileError
from patangoma.domain.models import TrackMetadata
from patangoma.services.audio_backend import AudioBackend

SUPPORTED_AUDIO_EXTENSIONS = {
    ".mp3",
    ".flac",
    ".m4a",
    ".ogg",
    ".wav",
    ".wma",
    ".aac",
    ".aiff",
    ".alac",
}


class ScanSummary(BaseModel):
    """Aggregated library inspection statistics."""

    total_files_scanned: int = 0
    valid_audio_files: int = 0
    corrupt_or_unreadable: int = 0
    missing_title_count: int = 0
    missing_artist_count: int = 0
    missing_album_count: int = 0
    missing_year_count: int = 0
    missing_artwork_count: int = 0
    duplicate_groups: list[list[str]] = Field(default_factory=list)
    errors: list[dict[str, str]] = Field(default_factory=list)


class LibraryScanner:
    """Discovers audio files and inspects library metadata health."""

    def __init__(self, backend: AudioBackend | None = None) -> None:
        self.backend = backend or AudioBackend()

    def discover_files(
        self, root_dir: str | Path, recursive: bool = True
    ) -> list[Path]:
        """Discover supported audio files in the given directory."""
        path = Path(root_dir)
        if not path.exists() or not path.is_dir():
            return []

        audio_files: list[Path] = []
        if recursive:
            for p in path.rglob("*"):
                if p.is_file() and p.suffix.lower() in SUPPORTED_AUDIO_EXTENSIONS:
                    audio_files.append(p)
        else:
            for p in path.glob("*"):
                if p.is_file() and p.suffix.lower() in SUPPORTED_AUDIO_EXTENSIONS:
                    audio_files.append(p)

        return sorted(audio_files)

    def scan_directory(
        self,
        root_dir: str | Path,
        recursive: bool = True,
    ) -> tuple[list[TrackMetadata], ScanSummary]:
        """Scan directory and return list of valid TrackMetadata and ScanSummary report."""
        files = self.discover_files(root_dir, recursive=recursive)
        summary = ScanSummary(total_files_scanned=len(files))
        tracks: list[TrackMetadata] = []

        signature_map: dict[tuple[str, str], list[str]] = defaultdict(list)

        for file_path in files:
            try:
                meta = self.backend.read_metadata(file_path)
                tracks.append(meta)
                summary.valid_audio_files += 1

                # Check missing attributes
                if not meta.title:
                    summary.missing_title_count += 1
                if not meta.artist:
                    summary.missing_artist_count += 1
                if not meta.album:
                    summary.missing_album_count += 1
                if not meta.year:
                    summary.missing_year_count += 1
                if not meta.has_artwork:
                    summary.missing_artwork_count += 1

                # Duplicate detection by title + artist
                if meta.title and meta.artist:
                    key = (meta.title.strip().lower(), meta.artist.strip().lower())
                    signature_map[key].append(str(file_path))

            except AudioFileError as e:
                summary.corrupt_or_unreadable += 1
                summary.errors.append({"file": str(file_path), "error": str(e)})

        # Populate duplicate groups
        for paths in signature_map.values():
            if len(paths) > 1:
                summary.duplicate_groups.append(paths)

        return tracks, summary
