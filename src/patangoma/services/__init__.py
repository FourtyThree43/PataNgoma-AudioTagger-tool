"""Application services package."""

from patangoma.services.aggregator import MetadataAggregator
from patangoma.services.ai_reasoner import FilenameInference, MetadataReasoner
from patangoma.services.album_matcher import AlbumAlignment, AlbumMatcher
from patangoma.services.artwork import ArtworkService
from patangoma.services.audio_backend import AudioBackend, compute_file_checksum
from patangoma.services.audit import AuditJournal, default_audit_db_path
from patangoma.services.batch import BatchPlan, BatchService
from patangoma.services.cache import (
    ProviderCache,
    cached_get_track,
    cached_search,
    default_provider_cache,
)
from patangoma.services.doctor import DoctorReport, run_diagnostics
from patangoma.services.duplicates import DuplicateDetector, DuplicateGroup
from patangoma.services.planner import PlanEngine
from patangoma.services.renamer import RenamerService, sanitize_filename_component
from patangoma.services.sample_generator import generate_sample_library
from patangoma.services.scanner import (
    SUPPORTED_AUDIO_EXTENSIONS,
    LibraryScanner,
    ScanSummary,
)
from patangoma.services.validator import FileIntegrityReport, FileValidator

__all__ = [
    "SUPPORTED_AUDIO_EXTENSIONS",
    "AlbumAlignment",
    "AlbumMatcher",
    "ArtworkService",
    "AudioBackend",
    "AuditJournal",
    "BatchPlan",
    "BatchService",
    "DoctorReport",
    "DuplicateDetector",
    "DuplicateGroup",
    "FileIntegrityReport",
    "FileValidator",
    "FilenameInference",
    "LibraryScanner",
    "MetadataAggregator",
    "MetadataReasoner",
    "PlanEngine",
    "ProviderCache",
    "RenamerService",
    "ScanSummary",
    "cached_get_track",
    "cached_search",
    "compute_file_checksum",
    "default_audit_db_path",
    "default_provider_cache",
    "generate_sample_library",
    "run_diagnostics",
    "sanitize_filename_component",
]
