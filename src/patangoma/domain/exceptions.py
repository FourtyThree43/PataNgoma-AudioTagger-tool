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
