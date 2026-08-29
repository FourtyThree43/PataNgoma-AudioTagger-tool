"""Base protocol and abstract class for metadata providers."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from patangoma.domain.models import MetadataCandidate, QueryParameters
from patangoma.plugins.contracts import PluginCapability


@runtime_checkable
class MetadataProvider(Protocol):
    """Protocol that all metadata providers must satisfy."""

    @property
    def name(self) -> str:
        """Provider unique name identifier."""
        ...

    def search_tracks(self, query: QueryParameters) -> list[MetadataCandidate]:
        """Search for track candidates matching the given query parameters."""
        ...

    def get_track_by_id(self, track_id: str) -> MetadataCandidate | None:
        """Fetch a specific track candidate by its provider-specific ID."""
        ...


class BaseMetadataProvider:
    """Base class providing default plugin lifecycle and capability implementations for providers."""

    _name: str = "base"
    _version: str = "1.0.0"

    @property
    def id(self) -> str:
        return self._name

    @property
    def name(self) -> str:
        return self._name

    @property
    def version(self) -> str:
        return self._version

    @property
    def capabilities(self) -> set[PluginCapability]:
        return {PluginCapability.METADATA}

    def health(self) -> dict[str, Any]:
        return {
            "status": "HEALTHY",
            "provider": self.name,
            "version": self.version,
        }

    def initialize(self) -> None:
        pass

    def shutdown(self) -> None:
        pass
