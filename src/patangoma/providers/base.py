"""Base protocol and abstract class for metadata providers."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from patangoma.domain.models import MetadataCandidate, QueryParameters


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
