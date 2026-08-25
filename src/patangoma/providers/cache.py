"""Lightweight, transparent caching layer for external metadata provider queries."""

from __future__ import annotations

import contextlib
import functools
import hashlib
import json
import logging
import os
import sqlite3
import tempfile
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any, TypeVar

import platformdirs
from cachetools import TTLCache

from patangoma.domain.models import MetadataCandidate, QueryParameters

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


def default_cache_db_path() -> Path:
    """Return default path to provider response SQLite cache conforming to OS standards via platformdirs."""
    if env_home := os.getenv("PATANGOMA_HOME"):
        return Path(env_home) / "provider_cache.db"
    try:
        cache_dir = Path(platformdirs.user_cache_dir("patangoma", appauthor=False))
        cache_dir.mkdir(parents=True, exist_ok=True)
        return cache_dir / "provider_cache.db"
    except OSError:
        tmp = Path(tempfile.gettempdir()) / ".patangoma"
        tmp.mkdir(parents=True, exist_ok=True)
        return tmp / "provider_cache.db"


def make_cache_key(provider: str, method: str, params: Any) -> str:
    """Compute a deterministic hash key for provider queries."""
    if isinstance(params, dict):
        raw = json.dumps(params, sort_keys=True, default=str)
    else:
        raw = str(params)
    hash_digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]
    return f"{provider}:{method}:{hash_digest}"


class ProviderCache:
    """Two-tier cache (in-memory TTLCache + persistent SQLite) for provider queries."""

    def __init__(
        self,
        db_path: str | Path | None = None,
        maxsize: int = 1000,
        default_ttl: int = 86400,  # 24 hours
    ) -> None:
        self.db_path = Path(db_path) if db_path else default_cache_db_path()
        self.default_ttl = default_ttl
        self._mem_cache: TTLCache[str, Any] = TTLCache(maxsize=maxsize, ttl=default_ttl)
        self._db_initialized = False

    def _get_connection(self) -> sqlite3.Connection | None:
        try:
            if not self._db_initialized:
                with contextlib.suppress(OSError):
                    self.db_path.parent.mkdir(parents=True, exist_ok=True)
                conn = sqlite3.connect(str(self.db_path))
                with conn:
                    conn.execute(
                        """
                        CREATE TABLE IF NOT EXISTS provider_cache (
                            cache_key TEXT PRIMARY KEY,
                            provider_name TEXT NOT NULL,
                            data_json TEXT NOT NULL,
                            expires_at REAL NOT NULL
                        )
                        """
                    )
                self._db_initialized = True
                return conn
            return sqlite3.connect(str(self.db_path))
        except (sqlite3.OperationalError, OSError):
            return None

    def get_cached_candidates(
        self, provider: str, method: str, params: Any
    ) -> list[MetadataCandidate] | None:
        """Retrieve cached list of MetadataCandidate, or None if miss/expired."""
        key = make_cache_key(provider, method, params)

        # 1. Check in-memory TTLCache
        if key in self._mem_cache:
            return self._mem_cache[key]

        # 2. Check SQLite cache
        conn = self._get_connection()
        if conn is None:
            return None

        try:
            with conn:
                cursor = conn.execute(
                    "SELECT data_json, expires_at FROM provider_cache WHERE cache_key = ?",
                    (key,),
                )
                row = cursor.fetchone()
                if row:
                    data_json, expires_at = row
                    if time.time() < expires_at:
                        parsed = json.loads(data_json)
                        candidates = [
                            MetadataCandidate.model_validate(item) for item in parsed
                        ]
                        self._mem_cache[key] = candidates
                        return candidates
                    else:
                        conn.execute(
                            "DELETE FROM provider_cache WHERE cache_key = ?", (key,)
                        )
        except Exception as e:
            logger.debug("Cache read error for key %s: %s", key, e)
        finally:
            conn.close()

        return None

    def set_cached_candidates(
        self,
        provider: str,
        method: str,
        params: Any,
        candidates: list[MetadataCandidate],
        ttl: int | None = None,
    ) -> None:
        """Store list of MetadataCandidate in memory and SQLite cache."""
        key = make_cache_key(provider, method, params)
        cache_ttl = ttl if ttl is not None else self.default_ttl
        expires_at = time.time() + cache_ttl

        # 1. Update in-memory TTLCache
        self._mem_cache[key] = candidates

        # 2. Update SQLite cache
        conn = self._get_connection()
        if conn is None:
            return

        try:
            serialized = json.dumps([c.model_dump(mode="json") for c in candidates])
            with conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO provider_cache (cache_key, provider_name, data_json, expires_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    (key, provider, serialized, expires_at),
                )
        except Exception as e:
            logger.debug("Cache write error for key %s: %s", key, e)
        finally:
            conn.close()

    def get_cached_candidate(
        self, provider: str, method: str, params: Any
    ) -> MetadataCandidate | None:
        """Retrieve single cached candidate, or None if miss/expired."""
        key = make_cache_key(provider, method, params)

        if key in self._mem_cache:
            return self._mem_cache[key]

        conn = self._get_connection()
        if conn is None:
            return None

        try:
            with conn:
                cursor = conn.execute(
                    "SELECT data_json, expires_at FROM provider_cache WHERE cache_key = ?",
                    (key,),
                )
                row = cursor.fetchone()
                if row:
                    data_json, expires_at = row
                    if time.time() < expires_at:
                        if data_json == "null":
                            return None
                        candidate = MetadataCandidate.model_validate(
                            json.loads(data_json)
                        )
                        self._mem_cache[key] = candidate
                        return candidate
                    else:
                        conn.execute(
                            "DELETE FROM provider_cache WHERE cache_key = ?", (key,)
                        )
        except Exception as e:
            logger.debug("Cache read error for key %s: %s", key, e)
        finally:
            conn.close()

        return None

    def set_cached_candidate(
        self,
        provider: str,
        method: str,
        params: Any,
        candidate: MetadataCandidate | None,
        ttl: int | None = None,
    ) -> None:
        """Store single candidate in memory and SQLite cache."""
        key = make_cache_key(provider, method, params)
        cache_ttl = ttl if ttl is not None else self.default_ttl
        expires_at = time.time() + cache_ttl

        self._mem_cache[key] = candidate

        conn = self._get_connection()
        if conn is None:
            return

        try:
            serialized = (
                json.dumps(candidate.model_dump(mode="json")) if candidate else "null"
            )
            with conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO provider_cache (cache_key, provider_name, data_json, expires_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    (key, provider, serialized, expires_at),
                )
        except Exception as e:
            logger.debug("Cache write error for key %s: %s", key, e)
        finally:
            conn.close()

    def clear(self) -> None:
        """Clear both in-memory and on-disk caches."""
        self._mem_cache.clear()
        conn = self._get_connection()
        if conn:
            try:
                with conn:
                    conn.execute("DELETE FROM provider_cache")
            finally:
                conn.close()


default_provider_cache = ProviderCache()


def cached_search(
    cache: ProviderCache | None = None,
) -> Callable[[F], F]:
    """Decorator to cache search_tracks provider methods."""

    def decorator(fn: F) -> F:
        @functools.wraps(fn)
        def wrapper(
            self: Any, query: QueryParameters, *args: Any, **kwargs: Any
        ) -> list[MetadataCandidate]:
            active_cache = cache or default_provider_cache
            query_dict = query.model_dump(mode="json")
            cached = active_cache.get_cached_candidates(
                self.name, "search_tracks", query_dict
            )
            if cached is not None:
                return cached
            results: list[MetadataCandidate] = fn(self, query, *args, **kwargs)
            active_cache.set_cached_candidates(
                self.name, "search_tracks", query_dict, results
            )
            return results

        return wrapper  # type: ignore[return-value]

    return decorator


def cached_get_track(
    cache: ProviderCache | None = None,
) -> Callable[[F], F]:
    """Decorator to cache get_track_by_id provider methods."""

    def decorator(fn: F) -> F:
        @functools.wraps(fn)
        def wrapper(
            self: Any, track_id: str, *args: Any, **kwargs: Any
        ) -> MetadataCandidate | None:
            active_cache = cache or default_provider_cache
            cached = active_cache.get_cached_candidate(
                self.name, "get_track_by_id", track_id
            )
            if cached is not None:
                return cached
            result: MetadataCandidate | None = fn(self, track_id, *args, **kwargs)
            active_cache.set_cached_candidate(
                self.name, "get_track_by_id", track_id, result
            )
            return result

        return wrapper  # type: ignore[return-value]

    return decorator
