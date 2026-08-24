"""Structured audio library file renamer and directory organizer."""

from __future__ import annotations

import re
import shutil
from pathlib import Path
from typing import Any

from patangoma.domain.exceptions import AudioFileNotFoundError
from patangoma.domain.models import TrackMetadata

# Characters forbidden in Windows and POSIX filenames
_ILLEGAL_FS_CHARS = re.compile(r"[\<\>\:\"\/\\\|\?\*]")


def sanitize_filename_component(name: str | None, fallback: str = "Unknown") -> str:
    """Sanitize a metadata string for safe use as a directory or filename component."""
    if not name or not name.strip():
        return fallback
    # Replace path separators and colons with hyphen
    clean = re.sub(r"[\/\\:]+", "-", name.strip())
    # Remove quotes, angle brackets, pipes, question marks, and asterisks
    clean = re.sub(r"[\<\>\"\|\?\*]+", "", clean)
    # Collapse spaces around hyphens and consecutive spaces
    clean = re.sub(r"\s*-\s*", "-", clean)
    clean = re.sub(r"\s+", " ", clean).strip(" .-")
    return clean or fallback


class RenamerService:
    """Safely formats and renames audio files according to template patterns."""

    DEFAULT_PATTERN = "{track_number:02d} - {artist} - {title}.{file_format}"
    ALBUM_PATTERN = "{album_artist}/{album}/{track_number:02d} - {title}.{file_format}"

    @staticmethod
    def render_pattern(
        track: TrackMetadata,
        pattern: str = DEFAULT_PATTERN,
    ) -> str:
        """Render a formatting pattern string using TrackMetadata attributes."""
        fmt = (track.file_format or Path(track.file_path).suffix.lstrip(".")).lower()
        track_num = track.track_number or 1

        context: dict[str, Any] = {
            "title": sanitize_filename_component(track.title, fallback="Untitled"),
            "artist": sanitize_filename_component(
                track.artist, fallback="Unknown Artist"
            ),
            "album": sanitize_filename_component(track.album, fallback="Unknown Album"),
            "album_artist": sanitize_filename_component(
                track.albumartist or track.artist, fallback="Unknown Artist"
            ),
            "year": track.year or 0,
            "genre": sanitize_filename_component(track.genre, fallback="Unknown Genre"),
            "track_number": track_num,
            "disc_number": track.disc_number or 1,
            "isrc": track.isrc or "",
            "file_format": fmt,
        }

        try:
            return pattern.format(**context)
        except (KeyError, ValueError):
            # Fallback formatting if template keys are invalid
            return f"{track_num:02d} - {context['artist']} - {context['title']}.{fmt}"

    def preview_rename(
        self,
        track: TrackMetadata,
        pattern: str = DEFAULT_PATTERN,
        target_root: str | Path | None = None,
    ) -> Path:
        """Calculate the target path without modifying filesystem."""
        orig_path = Path(track.file_path)
        rel_target = self.render_pattern(track, pattern=pattern)

        if target_root:
            return Path(target_root) / rel_target
        return orig_path.parent / rel_target

    def rename_track(
        self,
        track: TrackMetadata,
        pattern: str = DEFAULT_PATTERN,
        target_root: str | Path | None = None,
        dry_run: bool = False,
    ) -> tuple[Path, Path]:
        """Rename an audio file on disk, returning (original_path, new_path)."""
        orig_path = Path(track.file_path)
        if not orig_path.exists():
            raise AudioFileNotFoundError(
                "Audio file to rename not found", str(orig_path)
            )

        target_path = self.preview_rename(
            track, pattern=pattern, target_root=target_root
        )

        if orig_path.resolve() == target_path.resolve():
            return orig_path, target_path

        if not dry_run:
            target_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(orig_path), str(target_path))

        return orig_path, target_path
