"""Typed domain exceptions for PataNgoma."""

from __future__ import annotations


class PataNgomaError(Exception):
    """Base exception for all PataNgoma errors."""

    def __init__(self, message: str, details: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details

    def __str__(self) -> str:
        if self.details:
            return f"{self.message} ({self.details})"
        return self.message


class DomainError(PataNgomaError):
    """Base exception for pure domain errors."""


class AudioFileError(PataNgomaError):
    """Base exception for audio file processing issues."""


class AudioFileNotFoundError(AudioFileError):
    """Raised when an audio file cannot be found at the specified path."""


class InvalidAudioFileError(AudioFileError):
    """Raised when a file exists but is not a recognized or valid audio file."""


class CorruptAudioFileError(AudioFileError):
    """Raised when an audio file header or frame data is corrupted."""


class UnsupportedAudioFormatError(AudioFileError):
    """Raised when an audio format is not supported by PataNgoma."""


class TagReadError(AudioFileError):
    """Raised when metadata tags cannot be read from the file."""


class TagWriteError(AudioFileError):
    """Raised when metadata tags cannot be written to the file."""


class ProviderError(PataNgomaError):
    """Base exception for metadata provider errors."""


class ProviderUnavailableError(ProviderError):
    """Raised when a provider API is unreachable or times out."""


class ProviderAuthenticationError(ProviderError):
    """Raised when provider credentials (API keys, client secrets) are missing or invalid."""


class ProviderRateLimitError(ProviderError):
    """Raised when provider API rate limits are exceeded."""


class PlanError(PataNgomaError):
    """Base exception for Plan / Apply execution errors."""


class PlanValidationError(PlanError):
    """Raised when a plan fails validation before execution."""


class RollbackError(PataNgomaError):
    """Raised when restoring an audio file from backup history fails."""


class ValidationError(PataNgomaError):
    """Raised when domain entity or parameter validation fails."""


class NotFoundError(PataNgomaError):
    """Raised when a requested domain resource or record is not found."""


class ConflictError(PataNgomaError):
    """Raised when an operation encounters an entity or state conflict."""


class MatchingError(PataNgomaError):
    """Raised when candidate matching or similarity calculation encounters an error."""


class MetadataError(PataNgomaError):
    """Raised when metadata normalization, parsing, or extraction fails."""


class MediaError(PataNgomaError):
    """Raised when media operations or tools encounter a failure."""


class PluginError(PataNgomaError):
    """Base exception for plugin lifecycle and execution failures."""


class PluginNotFoundError(PluginError):
    """Raised when a requested plugin cannot be found or discovered."""


class PluginLoadError(PluginError):
    """Raised when a plugin fails to initialize or load its capabilities."""


class PersistenceError(PataNgomaError):
    """Base exception for repository and storage layer errors."""


class RepositoryError(PersistenceError):
    """Raised when a repository query, write, or transaction fails."""


class ConfigurationError(PataNgomaError):
    """Raised when application configuration is invalid or missing."""


class JobError(PataNgomaError):
    """Base exception for background job errors."""


class JobNotFoundError(JobError):
    """Raised when a job ID is not found in the job manager."""


class JobCancellationError(JobError):
    """Raised when an active job is cancelled."""
