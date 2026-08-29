"""Plugin contracts and capability definitions for PataNgoma platform."""

from __future__ import annotations

from collections.abc import Sequence
from enum import Enum
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from patangoma.domain.models import MetadataCandidate, QueryParameters


class PluginCapability(str, Enum):
    """Capabilities that plugins can declare and provide."""

    METADATA = "METADATA"
    DOWNLOAD = "DOWNLOAD"
    MEDIA_TOOL = "MEDIA_TOOL"
    ARTWORK = "ARTWORK"
    LYRICS = "LYRICS"
    IMPORTER = "IMPORTER"
    EXPORTER = "EXPORTER"


@runtime_checkable
class Plugin(Protocol):
    """Base interface that all PataNgoma plugins must satisfy."""

    @property
    def id(self) -> str:
        """Unique machine-readable identifier for the plugin (e.g. 'musicbrainz', 'spotify')."""
        ...

    @property
    def name(self) -> str:
        """Human-readable name of the plugin."""
        ...

    @property
    def version(self) -> str:
        """Plugin version string."""
        ...

    @property
    def capabilities(self) -> set[PluginCapability]:
        """Set of capabilities provided by this plugin."""
        ...

    def health(self) -> dict[str, Any]:
        """Diagnostic health status check of the plugin (connectivity, auth, dependencies)."""
        ...

    def initialize(self) -> None:
        """Lifecycle hook called when the plugin is loaded."""
        ...

    def shutdown(self) -> None:
        """Lifecycle hook called when the plugin is unloaded."""
        ...


@runtime_checkable
class MetadataProviderPlugin(Plugin, Protocol):
    """Plugin specialized in retrieving music metadata from external APIs or local databases."""

    def search_tracks(self, query: QueryParameters) -> Sequence[MetadataCandidate]:
        """Search tracks based on query parameters."""
        ...

    def get_track_by_id(self, track_id: str) -> MetadataCandidate | None:
        """Retrieve a specific track candidate by provider ID."""
        ...


@runtime_checkable
class DownloadBackendPlugin(Plugin, Protocol):
    """Plugin specialized in downloading media streams or files."""

    def download(
        self,
        url: str,
        destination_dir: Path,
        options: dict[str, Any] | None = None,
    ) -> Path:
        """Execute media download to target destination."""
        ...


@runtime_checkable
class MediaToolPlugin(Plugin, Protocol):
    """Plugin wrapping external media processing tools (e.g. ffmpeg, fpcalc)."""

    def is_available(self) -> bool:
        """Check if the external media binary is present and executable."""
        ...


@runtime_checkable
class ArtworkProviderPlugin(Plugin, Protocol):
    """Plugin specialized in cover artwork search and retrieval."""

    def search_artwork(self, album: str, artist: str, limit: int = 5) -> list[str]:
        """Return list of candidate image URLs for the given album and artist."""
        ...


@runtime_checkable
class LyricsProviderPlugin(Plugin, Protocol):
    """Plugin specialized in lyrics retrieval."""

    def fetch_lyrics(self, title: str, artist: str) -> str | None:
        """Retrieve plain or synchronized lyrics for a track."""
        ...
