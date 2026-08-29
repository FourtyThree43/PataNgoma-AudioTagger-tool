"""Lyrics retrieval and synchronized LRC provider adapter."""

from __future__ import annotations

import logging
from typing import Any

import requests

from patangoma.domain.models import MetadataCandidate, QueryParameters
from patangoma.providers.base import BaseMetadataProvider, MetadataProvider
from patangoma.providers.cache import cached_get_track, cached_search

logger = logging.getLogger(__name__)

_LRCLIB_GET_URL = "https://lrclib.net/api/get"
_LRCLIB_SEARCH_URL = "https://lrclib.net/api/search"


class LyricsProvider(BaseMetadataProvider, MetadataProvider):
    """Lyrics provider backed by LrcLib open-source REST API."""

    def __init__(self, session: requests.Session | None = None) -> None:
        self._name = "lyrics"
        self._session = session or requests.Session()
        self._session.headers.update(
            {
                "User-Agent": "PataNgoma/1.2.0 (https://github.com/FourtyThree43/PataNgoma-AudioTagger-tool)"
            }
        )

    @property
    def name(self) -> str:
        return self._name

    @cached_search()
    def search_tracks(self, query: QueryParameters) -> list[MetadataCandidate]:
        """Search LrcLib for tracks with available plain or synchronized lyrics."""
        if not query.title and not query.artist:
            return []

        params: dict[str, Any] = {}
        if query.title:
            params["track_name"] = query.title
        if query.artist:
            params["artist_name"] = query.artist
        if query.album:
            params["album_name"] = query.album

        try:
            resp = self._session.get(_LRCLIB_GET_URL, params=params, timeout=8.0)
            if resp.status_code == 404:
                # Fallback to search query
                q = f"{query.title or ''} {query.artist or ''}".strip()
                resp = self._session.get(
                    _LRCLIB_SEARCH_URL, params={"q": q}, timeout=8.0
                )

            if resp.status_code == 404:
                return []

            resp.raise_for_status()
            data = resp.json()
        except requests.RequestException as e:
            logger.debug("Lyrics fetch request error: %s", e)
            return []
        except Exception as e:
            logger.debug("Lyrics parsing error: %s", e)
            return []

        candidates: list[MetadataCandidate] = []
        if isinstance(data, list):
            for item in data[: query.limit]:
                cand = self._normalize_lyrics(item)
                if cand:
                    candidates.append(cand)
        elif isinstance(data, dict):
            cand = self._normalize_lyrics(data)
            if cand:
                candidates.append(cand)

        return candidates

    @cached_get_track()
    def get_track_by_id(self, track_id: str) -> MetadataCandidate | None:
        """Fetch lyrics record by LrcLib ID."""
        try:
            resp = self._session.get(
                f"https://lrclib.net/api/get/{track_id}", timeout=8.0
            )
            if resp.status_code == 404:
                return None
            resp.raise_for_status()
            return self._normalize_lyrics(resp.json())
        except Exception:
            return None

    def fetch_lyrics(
        self,
        title: str,
        artist: str,
        album: str | None = None,
        duration: float | None = None,
    ) -> tuple[str | None, str | None]:
        """Fetch (plain_lyrics, synced_lyrics) for a track."""
        cands = self.search_tracks(
            QueryParameters(title=title, artist=artist, album=album)
        )
        if not cands:
            return None, None

        payload = cands[0].raw_payload or {}
        plain = payload.get("plainLyrics")
        synced = payload.get("syncedLyrics")
        return plain, synced

    def _normalize_lyrics(self, raw: dict[str, Any]) -> MetadataCandidate | None:
        """Normalize LrcLib JSON response into a MetadataCandidate."""
        rec_id = str(raw.get("id") or "")
        title = raw.get("trackName")
        if not rec_id or not title:
            return None

        artist = raw.get("artistName", "Unknown Artist")
        plain = raw.get("plainLyrics")
        synced = raw.get("syncedLyrics")
        dur = raw.get("duration")

        return MetadataCandidate(
            provider_name="lyrics",
            provider_id=rec_id,
            title=title,
            artists=[artist],
            album=raw.get("albumName"),
            album_artist=artist,
            duration_seconds=float(dur) if dur else None,
            raw_payload={
                "plainLyrics": plain,
                "syncedLyrics": synced,
                "raw": raw,
            },
        )
