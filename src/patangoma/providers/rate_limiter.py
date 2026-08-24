"""Thread-safe rate limiting and request throttling for external metadata providers."""

from __future__ import annotations

import functools
import logging
import threading
import time
from collections.abc import Callable
from typing import Any, TypeVar

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])

# Default minimum interval (seconds) between successive calls to a provider
_DEFAULT_PROVIDER_INTERVALS: dict[str, float] = {
    "musicbrainz": 1.0,  # MusicBrainz guideline: 1 req/sec
    "discogs": 1.0,  # Discogs unauthenticated/authenticated standard limit
    "spotify": 0.1,  # Fast burst allowed
    "itunes": 0.2,  # iTunes search limit
    "deezer": 0.2,  # Deezer limit
}


class ProviderRateLimiter:
    """Thread-safe rate limiter managing per-provider request intervals."""

    def __init__(self, intervals: dict[str, float] | None = None) -> None:
        self._intervals = (
            intervals if intervals is not None else dict(_DEFAULT_PROVIDER_INTERVALS)
        )
        self._last_call: dict[str, float] = {}
        self._lock = threading.Lock()

    def acquire(self, provider_name: str) -> float:
        """Throttle execution if necessary to respect provider interval. Returns wait time."""
        interval = self._intervals.get(provider_name.lower(), 0.0)
        if interval <= 0.0:
            return 0.0

        with self._lock:
            now = time.time()
            last = self._last_call.get(provider_name.lower(), 0.0)
            elapsed = now - last
            wait_time = max(0.0, interval - elapsed)

            # Update scheduled completion time
            self._last_call[provider_name.lower()] = now + wait_time

        if wait_time > 0:
            time.sleep(wait_time)

        return wait_time

    def set_interval(self, provider_name: str, interval_seconds: float) -> None:
        """Update rate limit interval for a specific provider."""
        with self._lock:
            self._intervals[provider_name.lower()] = max(0.0, interval_seconds)


default_rate_limiter = ProviderRateLimiter()


def rate_limited(
    provider_name: str | None = None,
    limiter: ProviderRateLimiter | None = None,
) -> Callable[[F], F]:
    """Decorator to throttle API requests to external providers."""

    def decorator(fn: F) -> F:
        @functools.wraps(fn)
        def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
            active_limiter = limiter or default_rate_limiter
            name = provider_name or getattr(self, "name", "unknown")
            active_limiter.acquire(name)
            return fn(self, *args, **kwargs)

        return wrapper  # type: ignore[return-value]

    return decorator
