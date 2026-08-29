"""In-memory repository implementations for headless operations and testing."""

from __future__ import annotations

from typing import Any

from patangoma.domain.entities import Album, Track
from patangoma.domain.models import AuditRecord, JobDescriptor


class InMemoryTrackRepository:
    """In-memory storage for Track entities."""

    def __init__(self) -> None:
        self._tracks: dict[str, Track] = {}
        self._path_index: dict[str, str] = {}

    def save(self, track: Track) -> None:
        self._tracks[track.id] = track
        self._path_index[str(track.media_file.file_path)] = track.id

    def get_by_id(self, track_id: str) -> Track | None:
        return self._tracks.get(track_id)

    def get_by_path(self, file_path: str) -> Track | None:
        tid = self._path_index.get(file_path)
        return self._tracks.get(tid) if tid else None

    def list_all(self, limit: int = 1000) -> list[Track]:
        return list(self._tracks.values())[:limit]

    def delete(self, track_id: str) -> bool:
        track = self._tracks.pop(track_id, None)
        if track:
            self._path_index.pop(str(track.media_file.file_path), None)
            return True
        return False


class InMemoryAlbumRepository:
    """In-memory storage for Album entities."""

    def __init__(self) -> None:
        self._albums: dict[str, Album] = {}

    def save(self, album: Album) -> None:
        self._albums[album.id] = album

    def get_by_id(self, album_id: str) -> Album | None:
        return self._albums.get(album_id)

    def list_all(self, limit: int = 500) -> list[Album]:
        return list(self._albums.values())[:limit]


class InMemoryAuditRepository:
    """In-memory storage for AuditRecord journals."""

    def __init__(self) -> None:
        self._records: list[AuditRecord] = []
        self._by_op: dict[str, AuditRecord] = {}

    def record(self, entry: AuditRecord) -> None:
        self._records.append(entry)
        self._by_op[entry.operation_id] = entry

    def get_history(
        self, file_path: str | None = None, limit: int = 100
    ) -> list[AuditRecord]:
        if file_path:
            filtered = [r for r in self._records if r.file_path == file_path]
            return list(reversed(filtered))[:limit]
        return list(reversed(self._records))[:limit]

    def get_by_operation_id(self, operation_id: str) -> AuditRecord | None:
        return self._by_op.get(operation_id)


class InMemoryJobRepository:
    """In-memory storage for background JobDescriptors."""

    def __init__(self) -> None:
        self._jobs: dict[str, JobDescriptor] = {}

    def save(self, job: JobDescriptor) -> None:
        self._jobs[job.job_id] = job

    def get_by_id(self, job_id: str) -> JobDescriptor | None:
        return self._jobs.get(job_id)

    def list_all(self, limit: int = 100) -> list[JobDescriptor]:
        return list(self._jobs.values())[:limit]


class InMemoryConfigRepository:
    """In-memory configuration storage."""

    def __init__(self, initial: dict[str, Any] | None = None) -> None:
        self._data: dict[str, Any] = dict(initial or {})

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self._data[key] = value

    def get_all(self) -> dict[str, Any]:
        return dict(self._data)
