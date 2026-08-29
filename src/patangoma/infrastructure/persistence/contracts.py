"""Repository protocols for PataNgoma persistence layer."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from patangoma.domain.entities import Album, Track
from patangoma.domain.models import AuditRecord, JobDescriptor


@runtime_checkable
class TrackRepository(Protocol):
    """Protocol for persisting and retrieving audio track entities."""

    def save(self, track: Track) -> None: ...

    def get_by_id(self, track_id: str) -> Track | None: ...

    def get_by_path(self, file_path: str) -> Track | None: ...

    def list_all(self, limit: int = 1000) -> list[Track]: ...

    def delete(self, track_id: str) -> bool: ...


@runtime_checkable
class AlbumRepository(Protocol):
    """Protocol for persisting and retrieving album entities."""

    def save(self, album: Album) -> None: ...

    def get_by_id(self, album_id: str) -> Album | None: ...

    def list_all(self, limit: int = 500) -> list[Album]: ...


@runtime_checkable
class AuditRepository(Protocol):
    """Protocol for recording and querying transactional audit records."""

    def record(self, entry: AuditRecord) -> None: ...

    def get_history(
        self, file_path: str | None = None, limit: int = 100
    ) -> list[AuditRecord]: ...

    def get_by_operation_id(self, operation_id: str) -> AuditRecord | None: ...


@runtime_checkable
class JobRepository(Protocol):
    """Protocol for persisting and querying background job descriptors."""

    def save(self, job: JobDescriptor) -> None: ...

    def get_by_id(self, job_id: str) -> JobDescriptor | None: ...

    def list_all(self, limit: int = 100) -> list[JobDescriptor]: ...


@runtime_checkable
class ConfigRepository(Protocol):
    """Protocol for reading and saving configuration settings."""

    def get(self, key: str, default: Any = None) -> Any: ...

    def set(self, key: str, value: Any) -> None: ...

    def get_all(self) -> dict[str, Any]: ...
