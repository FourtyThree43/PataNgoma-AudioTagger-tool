"""Pure domain models for PataNgoma AudioTagger."""

from __future__ import annotations

import datetime as dt
import os
from enum import Enum
from pathlib import Path, PureWindowsPath
from typing import Any

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class ConfidenceLevel(str, Enum):
    """Confidence level of a match result."""

    EXACT = "EXACT"  # 95 - 100% confidence
    HIGH = "HIGH"  # 80 - 94% confidence
    MEDIUM = "MEDIUM"  # 60 - 79% confidence
    LOW = "LOW"  # 40 - 59% confidence
    NO_MATCH = "NO_MATCH"  # < 40% confidence


class FieldDiffStatus(str, Enum):
    """Status of an individual metadata tag modification."""

    ADDED = "ADDED"
    MODIFIED = "MODIFIED"
    REMOVED = "REMOVED"
    UNCHANGED = "UNCHANGED"


class QueryParameters(BaseModel):
    """Normalized query parameters for searching providers."""

    title: str | None = None
    artist: str | None = None
    album: str | None = None
    isrc: str | None = None
    year: int | None = None
    limit: int = Field(default=10, ge=1, le=50)

    model_config = ConfigDict(frozen=True)


class TrackMetadata(BaseModel):
    """Canonical representation of audio file tags and technical audio properties."""

    file_path: str
    file_format: str = "unknown"
    title: str | None = None
    artist: str | None = None
    artists: list[str] = Field(default_factory=list)
    album: str | None = None
    albumartist: str | None = None
    year: int | None = None
    date: dt.date | None = None
    genre: str | None = None
    genres: list[str] = Field(default_factory=list)
    track_number: int | None = None
    track_total: int | None = None
    disc_number: int | None = None
    disc_total: int | None = None
    isrc: str | None = None
    composer: str | None = None
    label: str | None = None
    comment: str | None = None
    lyrics: str | None = None

    # MusicBrainz IDs
    mb_trackid: str | None = None
    mb_artistid: str | None = None
    mb_albumid: str | None = None
    mb_albumartistid: str | None = None

    # Technical audio metadata
    duration_seconds: float | None = None
    bitrate: int | None = None
    sample_rate: int | None = None
    channels: int | None = None

    # Artwork metadata
    has_artwork: bool = False
    artwork_mime: str | None = None

    model_config = ConfigDict(extra="ignore")

    @property
    def path(self) -> Path:
        if "\\" in self.file_path and os.sep == "/":
            return Path(PureWindowsPath(self.file_path).as_posix())
        return Path(self.file_path)

    def to_tag_dict(self) -> dict[str, Any]:
        """Convert standard tags to a dictionary for tag writing."""
        tags: dict[str, Any] = {}
        fields = [
            "title",
            "artist",
            "album",
            "albumartist",
            "year",
            "date",
            "genre",
            "track_number",
            "track_total",
            "disc_number",
            "disc_total",
            "isrc",
            "composer",
            "label",
            "comment",
            "mb_trackid",
            "mb_artistid",
            "mb_albumid",
            "mb_albumartistid",
        ]
        for field in fields:
            val = getattr(self, field, None)
            if val is not None:
                # Map field name to mediafile property if needed
                if field == "track_number":
                    tags["track"] = val
                elif field == "track_total":
                    tags["tracktotal"] = val
                elif field == "disc_number":
                    tags["disc"] = val
                elif field == "disc_total":
                    tags["disctotal"] = val
                else:
                    tags[field] = val
        return tags


class MetadataCandidate(BaseModel):
    """Standardized candidate record returned from metadata providers."""

    provider_name: str
    provider_id: str
    title: str
    artists: list[str] = Field(default_factory=list)
    album: str | None = None
    album_artist: str | None = None
    release_date: dt.date | None = None
    year: int | None = None
    genres: list[str] = Field(default_factory=list)
    track_number: int | None = None
    track_total: int | None = None
    disc_number: int | None = None
    isrc: str | None = None
    label: str | None = None
    duration_seconds: float | None = None
    popularity: int | None = None
    artwork_url: str | None = None

    # MusicBrainz identifier links
    mb_trackid: str | None = None
    mb_artistid: str | None = None
    mb_albumid: str | None = None

    raw_payload: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="ignore")

    @property
    def primary_artist(self) -> str:
        return self.artists[0] if self.artists else ""

    def to_tag_dict(self) -> dict[str, Any]:
        """Convert candidate to update dictionary suitable for audio taggers."""
        tags: dict[str, Any] = {
            "title": self.title,
            "artist": self.primary_artist,
        }
        if self.album:
            tags["album"] = self.album
        if self.album_artist:
            tags["albumartist"] = self.album_artist
        if self.year:
            tags["year"] = self.year
        if self.release_date:
            tags["date"] = self.release_date
        if self.genres:
            tags["genre"] = self.genres[0]
        if self.track_number is not None:
            tags["track"] = self.track_number
        if self.track_total is not None:
            tags["tracktotal"] = self.track_total
        if self.disc_number is not None:
            tags["disc"] = self.disc_number
        if self.isrc:
            tags["isrc"] = self.isrc
        if self.label:
            tags["label"] = self.label
        if self.mb_trackid:
            tags["mb_trackid"] = self.mb_trackid
        if self.mb_artistid:
            tags["mb_artistid"] = self.mb_artistid
        if self.mb_albumid:
            tags["mb_albumid"] = self.mb_albumid

        return tags


class ScoreBreakdown(BaseModel):
    """Detailed explainable score components for a match."""

    title_score: float = Field(default=0.0, ge=0.0, le=1.0)
    artist_score: float = Field(default=0.0, ge=0.0, le=1.0)
    album_score: float = Field(default=0.0, ge=0.0, le=1.0)
    duration_score: float = Field(default=0.0, ge=0.0, le=1.0)
    total_score: float = Field(default=0.0, ge=0.0, le=1.0)
    reasons: list[str] = Field(
        default_factory=list,
        validation_alias=AliasChoices("reasons", "breakdown_reasons"),
    )

    @property
    def breakdown_reasons(self) -> list[str]:
        return self.reasons

    model_config = ConfigDict(frozen=True)


class MatchResult(BaseModel):
    """Evaluated match between local track and external candidate."""

    track_path: str = ""
    candidate: MetadataCandidate
    score: ScoreBreakdown
    confidence: ConfidenceLevel

    model_config = ConfigDict(frozen=True)

    @property
    def is_acceptable(self) -> bool:
        """Returns True if match confidence meets standard safe threshold."""
        return self.confidence in (ConfidenceLevel.EXACT, ConfidenceLevel.HIGH)


class TagFieldDiff(BaseModel):
    """Difference for an individual tag field."""

    field_name: str
    old_value: Any
    new_value: Any
    status: FieldDiffStatus

    model_config = ConfigDict(frozen=True)


class TagPlan(BaseModel):
    """Deterministic, actionable mutation plan for an audio file."""

    file_path: str
    provider_name: str
    provider_id: str
    confidence: ConfidenceLevel
    total_score: float
    diffs: list[TagFieldDiff]
    checksum_pre: str
    created_at: dt.datetime = Field(
        default_factory=lambda: dt.datetime.now(dt.timezone.utc)
    )

    model_config = ConfigDict(extra="ignore")

    @property
    def has_changes(self) -> bool:
        return any(d.status != FieldDiffStatus.UNCHANGED for d in self.diffs)


class AuditRecord(BaseModel):
    """Audit log record for transactional recovery and rollback."""

    operation_id: str
    timestamp: dt.datetime = Field(
        default_factory=lambda: dt.datetime.now(dt.timezone.utc)
    )
    file_path: str
    checksum_before: str
    checksum_after: str
    backup_tags: dict[str, Any]
    applied_tags: dict[str, Any]

    model_config = ConfigDict(extra="ignore")
