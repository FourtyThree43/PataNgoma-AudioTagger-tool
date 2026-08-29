"""Infrastructure package containing persistence, subprocess runners, media I/O, config, and logging."""

from patangoma.infrastructure.configuration.manager import (
    ConfigurationManager,
    default_config_path,
)
from patangoma.infrastructure.logging.logger import StructuredLogger, get_logger
from patangoma.infrastructure.media.backend import (
    AudioBackendPort,
    MediaFileAudioBackend,
    compute_file_checksum,
)
from patangoma.infrastructure.persistence.contracts import (
    AlbumRepository,
    AuditRepository,
    ConfigRepository,
    JobRepository,
    TrackRepository,
)
from patangoma.infrastructure.persistence.memory_repo import (
    InMemoryAlbumRepository,
    InMemoryAuditRepository,
    InMemoryConfigRepository,
    InMemoryJobRepository,
    InMemoryTrackRepository,
)
from patangoma.infrastructure.persistence.sqlite_repo import (
    SQLiteAuditRepository,
    SQLiteJobRepository,
)
from patangoma.infrastructure.subprocess.runner import ProcessResult, ProcessRunner

__all__ = [
    "AlbumRepository",
    "AudioBackendPort",
    "AuditRepository",
    "ConfigRepository",
    "ConfigurationManager",
    "InMemoryAlbumRepository",
    "InMemoryAuditRepository",
    "InMemoryConfigRepository",
    "InMemoryJobRepository",
    "InMemoryTrackRepository",
    "JobRepository",
    "MediaFileAudioBackend",
    "ProcessResult",
    "ProcessRunner",
    "SQLiteAuditRepository",
    "SQLiteJobRepository",
    "StructuredLogger",
    "TrackRepository",
    "compute_file_checksum",
    "default_config_path",
    "get_logger",
]
