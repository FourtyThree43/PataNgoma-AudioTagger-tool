"""Pure domain entities for PataNgoma platform."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from patangoma.domain.models import TrackMetadata


@dataclass
class MediaFileRef:
    """Descriptor of a physical audio file on the filesystem."""

    file_path: Path
    file_format: str
    file_size_bytes: int = 0
    checksum_sha256: str = ""
    duration_seconds: float | None = None
    bitrate_kbps: int | None = None
    sample_rate_hz: int | None = None
    channels: int | None = None

    @property
    def extension(self) -> str:
        return self.file_path.suffix.lstrip(".").lower()

    @property
    def filename(self) -> str:
        return self.file_path.name


@dataclass
class Artwork:
    """Domain model for embedded or external cover art."""

    data: bytes = field(repr=False, default=b"")
    mime_type: str = "image/jpeg"
    width: int | None = None
    height: int | None = None
    description: str = "Front Cover"
    source_url: str | None = None
    provider_name: str | None = None

    @property
    def size_bytes(self) -> int:
        return len(self.data)

    @property
    def is_valid(self) -> bool:
        return len(self.data) > 0


@dataclass
class Track:
    """Logical audio track entity combining media file reference and tags."""

    id: str
    media_file: MediaFileRef
    metadata: TrackMetadata
    status: str = "UNTAGGED"
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    extra: dict[str, Any] = field(default_factory=dict)

    @property
    def display_title(self) -> str:
        return self.metadata.title or self.media_file.filename

    @property
    def display_artist(self) -> str:
        return self.metadata.artist or "Unknown Artist"

    @property
    def display_album(self) -> str:
        return self.metadata.album or "Unknown Album"


@dataclass
class Artist:
    """Domain entity representing a music artist."""

    id: str
    name: str
    mb_artistid: str | None = None
    spotify_id: str | None = None
    genres: list[str] = field(default_factory=list)
    bio: str | None = None


@dataclass
class Album:
    """Logical album entity aggregating multiple tracks."""

    id: str
    title: str
    artist: str
    album_artist: str | None = None
    year: int | None = None
    release_date: date | None = None
    genre: str | None = None
    genres: list[str] = field(default_factory=list)
    tracks: list[Track] = field(default_factory=list)
    total_tracks: int | None = None
    total_discs: int | None = None
    artwork: Artwork | None = None
    mb_albumid: str | None = None
    spotify_id: str | None = None
    label: str | None = None

    @property
    def track_count(self) -> int:
        return len(self.tracks)

    @property
    def duration_seconds(self) -> float:
        return sum(
            t.media_file.duration_seconds or 0.0
            for t in self.tracks
            if t.media_file.duration_seconds is not None
        )
