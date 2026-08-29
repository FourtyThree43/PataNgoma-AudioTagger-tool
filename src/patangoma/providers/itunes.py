"""iTunes Search API metadata provider adapter."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

import requests

from patangoma.domain.exceptions import ProviderError, ProviderUnavailableError
from patangoma.domain.models import MetadataCandidate, QueryParameters
from patangoma.providers.base import BaseMetadataProvider, MetadataProvider
from patangoma.providers.cache import cached_get_track, cached_search

logger = logging.getLogger(__name__)

_ITUNES_SEARCH_URL = "https://itunes.apple.com/search"
_ITUNES_LOOKUP_URL = "https://itunes.apple.com/lookup"


class ITunesProvider(BaseMetadataProvider, MetadataProvider):
    """Metadata provider backed by Apple iTunes Search API (no API key required)."""

    def __init__(self, session: requests.Session | None = None) -> None:
        self._name = "itunes"
        self._session = session or requests.Session()

    @property
    def name(self) -> str:
        return self._name

    @cached_search()
    def search_tracks(self, query: QueryParameters) -> list[MetadataCandidate]:
        """Search tracks via iTunes Search API."""
        terms: list[str] = []
        if query.title:
            terms.append(query.title)
        if query.artist:
            terms.append(query.artist)
        if query.album and not terms:
            terms.append(query.album)

        if not terms and not query.isrc:
            return []

        search_term = " ".join(terms) if terms else (query.isrc or "")

        params = {
            "term": search_term,
            "media": "music",
            "entity": "song",
            "limit": min(query.limit, 50),
        }

        try:
            resp = self._session.get(_ITUNES_SEARCH_URL, params=params, timeout=10.0)
            resp.raise_for_status()
            data = resp.json()
        except requests.RequestException as e:
            logger.error("iTunes Search API error: %s", e)
            raise ProviderUnavailableError("iTunes API search failed", str(e)) from e
        except Exception as e:
            logger.error("Error parsing iTunes search response: %s", e)
            raise ProviderError("Failed to parse iTunes search results", str(e)) from e

        results = data.get("results", [])
        candidates: list[MetadataCandidate] = []
        for raw in results:
            cand = self._normalize_track(raw)
            if cand:
                candidates.append(cand)

        return candidates

    @cached_get_track()
    def get_track_by_id(self, track_id: str) -> MetadataCandidate | None:
        """Fetch track by iTunes trackId."""
        params = {"id": track_id, "entity": "song"}
        try:
            resp = self._session.get(_ITUNES_LOOKUP_URL, params=params, timeout=10.0)
            resp.raise_for_status()
            data = resp.json()
        except requests.RequestException as e:
            logger.error("iTunes lookup API error for ID %s: %s", track_id, e)
            raise ProviderUnavailableError("iTunes lookup failed", str(e)) from e
        except Exception as e:
            logger.error("Error during iTunes track lookup: %s", e)
            raise ProviderError("Failed to fetch from iTunes", str(e)) from e

        results = data.get("results", [])
        if results:
            return self._normalize_track(results[0])
        return None

    def _normalize_track(self, raw: dict[str, Any]) -> MetadataCandidate | None:
        """Normalize iTunes raw JSON item into a standard MetadataCandidate."""
        track_id = str(raw.get("trackId") or raw.get("collectionId") or "")
        title = raw.get("trackName")
        if not track_id or not title:
            return None

        artist_name = raw.get("artistName", "Unknown Artist")
        artists = [artist_name]
        album = raw.get("collectionName")

        # Parse release date and year
        release_date_str = raw.get("releaseDate")
        rel_date = None
        year = None
        if release_date_str:
            try:
                dt = datetime.fromisoformat(release_date_str.replace("Z", "+00:00"))
                rel_date = dt.date()
                year = dt.year
            except (ValueError, TypeError):
                pass

        # Duration
        millis = raw.get("trackTimeMillis")
        dur_sec = float(millis) / 1000.0 if millis else None

        # Genres
        genre = raw.get("primaryGenreName")
        genres = [genre] if genre else []

        # Artwork: Convert 100x100 url to 600x600 high-res
        art_url = raw.get("artworkUrl100")
        if art_url and "100x100" in art_url:
            art_url = art_url.replace("100x100", "600x600")

        return MetadataCandidate(
            provider_name="itunes",
            provider_id=track_id,
            title=title,
            artists=artists,
            album=album,
            album_artist=artist_name,
            release_date=rel_date,
            year=year,
            genres=genres,
            track_number=raw.get("trackNumber"),
            track_total=raw.get("trackCount"),
            disc_number=raw.get("discNumber"),
            duration_seconds=dur_sec,
            artwork_url=art_url,
            raw_payload=raw,
        )
