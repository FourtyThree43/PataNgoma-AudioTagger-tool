"""Structured logging system for PataNgoma platform."""

from __future__ import annotations

import logging
from typing import Any


class StructuredLogger:
    """Platform logger providing structured contextual logging."""

    def __init__(self, name: str = "patangoma") -> None:
        self._logger = logging.getLogger(name)

    def log(
        self,
        level: int,
        message: str,
        *,
        job_id: str | None = None,
        track_id: str | None = None,
        provider_id: str | None = None,
        **extra: Any,
    ) -> None:
        context = {k: v for k, v in extra.items() if v is not None}
        if job_id:
            context["job_id"] = job_id
        if track_id:
            context["track_id"] = track_id
        if provider_id:
            context["provider_id"] = provider_id

        if context:
            ctx_str = " ".join(f"[{k}={v}]" for k, v in context.items())
            self._logger.log(level, f"{ctx_str} {message}")
        else:
            self._logger.log(level, message)

    def info(self, message: str, **kwargs: Any) -> None:
        self.log(logging.INFO, message, **kwargs)

    def warning(self, message: str, **kwargs: Any) -> None:
        self.log(logging.WARNING, message, **kwargs)

    def error(self, message: str, **kwargs: Any) -> None:
        self.log(logging.ERROR, message, **kwargs)

    def debug(self, message: str, **kwargs: Any) -> None:
        self.log(logging.DEBUG, message, **kwargs)


def get_logger(name: str = "patangoma") -> StructuredLogger:
    return StructuredLogger(name)
