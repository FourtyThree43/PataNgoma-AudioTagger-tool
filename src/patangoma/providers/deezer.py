"""Deezer metadata provider adapter."""

from __future__ import annotations

import logging
from datetime import date, datetime
from typing import Any

import deezer

from patangoma.domain.exceptions import ProviderError, ProviderUnavailableError
from patangoma.domain.models import MetadataCandidate, QueryParameters
from patangoma.providers.base import BaseMetadataProvider, MetadataProvider
from patangoma.providers.cache import cached_get_track, cached_search

logger = logging.getLogger(__name__)


class DeezerProvider(BaseMetadataProvider, MetadataProvider):
    """Metadata provider backed by Deezer API."""

    def __init__(self, client: deezer.Client | None = None) -> None:
        self._name = "deezer"
        self._client = client or deezer.Client()

    @property
    def name(self) -> str:
        return self._name

    @cached_search()
    def search_tracks(self, query: QueryParameters) -> list[MetadataCandidate]:
        """Search tracks on Deezer and return normalized candidates."""
        parts = []
        if query.title:
            parts.append(f'track:"{query.title}"')
        if query.artist:
            parts.append(f'artist:"{query.artist}"')
        if query.album:
            parts.append(f'album:"{query.album}"')

        if not parts and not query.isrc:
            return []

        search_str = " ".join(parts) if parts else f'isrc:"{query.isrc}"'

        try:
            results = self._client.search(search_str)
            candidates: list[MetadataCandidate] = []
            for item in list(results)[: query.limit]:
                track_dict = item.as_dict()
                candidate = self._normalize_track(track_dict)
                if candidate:
                    candidates.append(candidate)
            return candidates
        except Exception as e:
            logger.error("Deezer search failed for '%s': %s", search_str, e)
            raise ProviderUnavailableError(
                "Deezer search request failed", str(e)
            ) from e

    @cached_get_track()
    def get_track_by_id(self, track_id: str) -> MetadataCandidate | None:
        """Fetch Deezer track by its integer track ID."""
        try:
            track = self._client.get_track(int(track_id))
            if track:
                return self._normalize_track(track.as_dict())
        except Exception as e:
            logger.error("Deezer get_track_by_id failed for %s: %s", track_id, e)
            raise ProviderError("Failed to fetch track from Deezer", str(e)) from e
        return None

    def _normalize_track(self, raw: dict[str, Any]) -> MetadataCandidate | None:
        """Normalize Deezer API track dictionary into a MetadataCandidate."""
        track_id = str(raw.get("id", ""))
        title = raw.get("title", "")
        if not track_id or not title:
            return None

        # Artists
        artists: list[str] = []
        if raw.get("contributors"):
            artists = [
                c.get("name")
                for c in raw["contributors"]
                if isinstance(c, dict) and "name" in c
            ]
        if not artists and "artist" in raw and isinstance(raw["artist"], dict):
            artists = [raw["artist"].get("name", "Unknown Artist")]
        if not artists:
            artists = ["Unknown Artist"]

        # Album
        album_data = raw.get("album", {})
        album_title = album_data.get("title") if isinstance(album_data, dict) else None
        artwork_url = (
            album_data.get("cover_big")
            or album_data.get("cover_xl")
            or album_data.get("cover_medium")
            if isinstance(album_data, dict)
            else None
        )

        # Release Date
        release_date_val: date | None = None
        year_val: int | None = None
        release_date_str = raw.get("release_date") or (
            album_data.get("release_date") if isinstance(album_data, dict) else None
        )
        if release_date_str:
            try:
                dt = datetime.strptime(str(release_date_str), "%Y-%m-%d")
                release_date_val = dt.date()
                year_val = dt.year
            except ValueError:
                pass

        # Duration
        duration_sec = float(raw.get("duration", 0)) if raw.get("duration") else None

        return MetadataCandidate(
            provider_name="deezer",
            provider_id=track_id,
            title=title,
            artists=artists,
            album=album_title,
            album_artist=artists[0] if artists else None,
            release_date=release_date_val,
            year=year_val,
            track_number=raw.get("track_position"),
            disc_number=raw.get("disk_number"),
            isrc=raw.get("isrc"),
            duration_seconds=duration_sec,
            popularity=raw.get("rank"),
            artwork_url=artwork_url,
            raw_payload=raw,
        )
