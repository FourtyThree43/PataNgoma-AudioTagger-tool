"""Audio metadata extraction and mutation backend using MediaFile/Mutagen."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from mediafile import MediaFile, UnreadableFileError

from patangoma.domain.exceptions import (
    AudioFileNotFoundError,
    CorruptAudioFileError,
    InvalidAudioFileError,
    TagReadError,
    TagWriteError,
)
from patangoma.domain.models import TrackMetadata


def compute_file_checksum(file_path: str | Path) -> str:
    """Compute SHA-256 checksum of the specified audio file."""
    path = Path(file_path)
    if not path.exists() or not path.is_file():
        raise AudioFileNotFoundError("Audio file does not exist", str(path))

    hasher = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


class AudioBackend:
    """Service to safely read and write audio metadata with integrity checks."""

    def read_metadata(self, file_path: str | Path) -> TrackMetadata:
        """Extract canonical TrackMetadata from an audio file."""
        path = Path(file_path)
        if not path.exists() or not path.is_file():
            raise AudioFileNotFoundError("Audio file not found", str(path))

        try:
            mf = MediaFile(str(path))
        except UnreadableFileError as e:
            raise InvalidAudioFileError(
                "Unreadable or invalid audio format", str(e)
            ) from e
        except Exception as e:
            raise CorruptAudioFileError(
                "Failed to parse audio file metadata", str(e)
            ) from e

        try:
            artists_list = [mf.artist] if mf.artist else []
            genres_list = [mf.genre] if mf.genre else []
            has_art = bool(getattr(mf, "art", None))
            fmt = (mf.format or path.suffix.lstrip(".")).lower()

            return TrackMetadata(
                file_path=str(path.resolve()),
                file_format=fmt,
                title=mf.title,
                artist=mf.artist,
                artists=artists_list,
                album=mf.album,
                albumartist=mf.albumartist,
                year=mf.year,
                date=getattr(mf, "date", None),
                genre=getattr(mf, "genre", None),
                genres=genres_list,
                track_number=getattr(mf, "track", None),
                track_total=getattr(mf, "tracktotal", None),
                disc_number=getattr(mf, "disc", None),
                disc_total=getattr(mf, "disctotal", None),
                isrc=getattr(mf, "isrc", None),
                composer=getattr(mf, "composer", None),
                label=getattr(mf, "label", None),
                comment=getattr(mf, "comments", getattr(mf, "comment", None)),
                lyrics=getattr(mf, "lyrics", None),
                mb_trackid=getattr(mf, "mb_trackid", None),
                mb_artistid=getattr(mf, "mb_artistid", None),
                mb_albumid=getattr(mf, "mb_albumid", None),
                mb_albumartistid=getattr(mf, "mb_albumartistid", None),
                duration_seconds=getattr(mf, "length", None),
                bitrate=getattr(mf, "bitrate", None),
                sample_rate=getattr(mf, "samplerate", None),
                channels=getattr(mf, "channels", None),
                has_artwork=has_art,
            )
        except Exception as e:
            raise TagReadError("Error extracting metadata properties", str(e)) from e

    def write_tags(
        self,
        file_path: str | Path,
        tags: dict[str, Any],
        dry_run: bool = False,
    ) -> TrackMetadata:
        """Write tag updates to audio file and return updated TrackMetadata."""
        path = Path(file_path)
        if not path.exists() or not path.is_file():
            raise AudioFileNotFoundError("Audio file not found", str(path))

        if dry_run:
            # In dry-run mode, simulate metadata update in-memory
            current = self.read_metadata(path)
            current_dict = current.model_dump()
            current_dict.update({k: v for k, v in tags.items() if hasattr(current, k)})
            return TrackMetadata(**current_dict)

        try:
            from datetime import datetime

            mf = MediaFile(str(path))
            for key, value in tags.items():
                if hasattr(mf, key):
                    if key == "date" and isinstance(value, str):
                        try:
                            value = datetime.strptime(value, "%Y-%m-%d").date()
                        except ValueError:
                            try:
                                value = datetime.strptime(value, "%Y").date()
                            except ValueError:
                                continue
                    setattr(mf, key, value)
            mf.save()
        except Exception as e:
            raise TagWriteError(
                f"Failed to write metadata tags to {path.name}", str(e)
            ) from e

        # Re-read from disk to guarantee post-mutation verification
        return self.read_metadata(path)
