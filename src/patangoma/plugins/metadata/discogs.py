"""Discogs metadata provider plugin."""

from __future__ import annotations

import contextlib
import logging
import os
from typing import Any

import requests
from dotenv import load_dotenv

from patangoma.domain.exceptions import (
    ProviderAuthenticationError,
    ProviderError,
    ProviderUnavailableError,
)
from patangoma.domain.models import MetadataCandidate, QueryParameters
from patangoma.plugins.contracts import MetadataProviderPlugin, PluginCapability
from patangoma.providers.base import BaseMetadataProvider
from patangoma.providers.cache import cached_get_track, cached_search

logger = logging.getLogger(__name__)

_DISCOGS_SEARCH_URL = "https://api.discogs.com/database/search"
_DISCOGS_RELEASE_URL = "https://api.discogs.com/releases"


class DiscogsPlugin(BaseMetadataProvider, MetadataProviderPlugin):
    """Metadata provider plugin backed by Discogs REST API."""

    def __init__(
        self,
        token: str | None = None,
        session: requests.Session | None = None,
    ) -> None:
        load_dotenv()
        self._name = "discogs"
        self._token = token or os.getenv("DISCOGS_TOKEN")
        self._session = session or requests.Session()
        self._session.headers.update(
            {
                "User-Agent": "PataNgoma/1.0.0 (https://github.com/FourtyThree43/PataNgoma-AudioTagger-tool)",
            }
        )
        if self._token:
            self._session.headers.update(
                {"Authorization": f"Discogs token={self._token}"}
            )

    @property
    def name(self) -> str:
        return self._name

    @property
    def capabilities(self) -> set[PluginCapability]:
        return {PluginCapability.METADATA}

    @cached_search()
    def search_tracks(self, query: QueryParameters) -> list[MetadataCandidate]:
        """Search Discogs database for matching releases / tracks."""
        params: dict[str, Any] = {"type": "release", "per_page": min(query.limit, 25)}
        if query.title:
            params["track"] = query.title
        if query.artist:
            params["artist"] = query.artist
        if query.album:
            params["release_title"] = query.album
        if query.year:
            params["year"] = query.year

        if len(params) <= 2 and not query.isrc:
            return []

        try:
            resp = self._session.get(_DISCOGS_SEARCH_URL, params=params, timeout=10.0)
            if resp.status_code == 401:
                raise ProviderAuthenticationError(
                    "Discogs authentication required or token invalid",
                    "Please provide a valid DISCOGS_TOKEN environment variable.",
                )
            resp.raise_for_status()
            data = resp.json()
        except ProviderAuthenticationError:
            raise
        except requests.RequestException as e:
            logger.error("Discogs API error: %s", e)
            raise ProviderUnavailableError("Discogs API request failed", str(e)) from e
        except Exception as e:
            logger.error("Error searching Discogs: %s", e)
            raise ProviderError("Failed to search Discogs", str(e)) from e

        results = data.get("results", [])
        candidates: list[MetadataCandidate] = []
        for raw in results:
            cand = self._normalize_search_result(raw, query_title=query.title)
            if cand:
                candidates.append(cand)

        return candidates

    @cached_get_track()
    def get_track_by_id(self, track_id: str) -> MetadataCandidate | None:
        """Fetch release by Discogs release ID."""
        url = f"{_DISCOGS_RELEASE_URL}/{track_id}"
        try:
            resp = self._session.get(url, timeout=10.0)
            if resp.status_code == 401:
                raise ProviderAuthenticationError(
                    "Discogs authentication failed", "Invalid DISCOGS_TOKEN"
                )
            if resp.status_code == 404:
                return None
            resp.raise_for_status()
            data = resp.json()
            return self._normalize_release_data(data)
        except ProviderAuthenticationError:
            raise
        except requests.RequestException as e:
            logger.error("Discogs lookup error for ID %s: %s", track_id, e)
            raise ProviderUnavailableError("Discogs lookup failed", str(e)) from e
        except Exception as e:
            logger.error("Error during Discogs lookup: %s", e)
            raise ProviderError("Failed to fetch from Discogs", str(e)) from e

    def _normalize_search_result(
        self, raw: dict[str, Any], query_title: str | None = None
    ) -> MetadataCandidate | None:
        """Normalize search result from Discogs search endpoint."""
        rel_id = str(raw.get("id") or "")
        full_title = raw.get("title", "")
        if not rel_id or not full_title:
            return None

        # Discogs search results format title as "Artist - Title" or "Artist - Release"
        artist_name = "Unknown Artist"
        title = full_title
        if " - " in full_title:
            parts = full_title.split(" - ", 1)
            artist_name = parts[0].strip()
            title = parts[1].strip()

        # When searching for a track, prioritize the specific query track title
        if query_title:
            title = query_title

        year_val = None
        if raw.get("year"):
            with contextlib.suppress(ValueError, TypeError):
                year_val = int(raw.get("year"))

        genres = raw.get("genre", []) + raw.get("style", [])
        cover_image = raw.get("cover_image") or raw.get("thumb")

        return MetadataCandidate(
            provider_name="discogs",
            provider_id=rel_id,
            title=title,
            artists=[artist_name],
            album=full_title if " - " in full_title else raw.get("title"),
            album_artist=artist_name,
            year=year_val,
            genres=genres[:5] if genres else [],
            artwork_url=cover_image
            if cover_image and not cover_image.endswith("spacer.gif")
            else None,
            raw_payload=raw,
        )

    def _normalize_release_data(self, raw: dict[str, Any]) -> MetadataCandidate | None:
        """Normalize full release payload from Discogs releases endpoint."""
        rel_id = str(raw.get("id") or "")
        title = raw.get("title", "")
        if not rel_id or not title:
            return None

        artists_list = [
            a.get("name", "") for a in raw.get("artists", []) if a.get("name")
        ]
        artist_name = artists_list[0] if artists_list else "Unknown Artist"

        year_val = raw.get("year")
        genres = raw.get("genres", []) + raw.get("styles", [])

        images = raw.get("images", [])
        art_url = images[0].get("uri") if images else None

        return MetadataCandidate(
            provider_name="discogs",
            provider_id=rel_id,
            title=title,
            artists=artists_list if artists_list else [artist_name],
            album=title,
            album_artist=artist_name,
            year=int(year_val) if year_val else None,
            genres=genres[:5] if genres else [],
            artwork_url=art_url,
            raw_payload=raw,
        )


# Backward compatibility alias
DiscogsProvider = DiscogsPlugin
