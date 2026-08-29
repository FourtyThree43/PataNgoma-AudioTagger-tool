"""Spotify metadata provider adapter."""

from __future__ import annotations

import logging
import os
from datetime import date, datetime
from typing import Any

import spotipy
from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyClientCredentials, SpotifyOauthError

from patangoma.domain.exceptions import (
    ProviderAuthenticationError,
    ProviderError,
    ProviderUnavailableError,
)
from patangoma.domain.models import MetadataCandidate, QueryParameters
from patangoma.providers.base import BaseMetadataProvider, MetadataProvider
from patangoma.providers.cache import cached_get_track, cached_search

logger = logging.getLogger(__name__)


class SpotifyProvider(BaseMetadataProvider, MetadataProvider):
    """Metadata provider backed by Spotify Web API."""

    def __init__(
        self,
        client_id: str | None = None,
        client_secret: str | None = None,
        sp_client: spotipy.Spotify | None = None,
    ) -> None:
        load_dotenv()
        self._name = "spotify"
        self._client_id = client_id or os.getenv("SPOTIPY_CLIENT_ID")
        self._client_secret = client_secret or os.getenv("SPOTIPY_CLIENT_SECRET")
        self._client = sp_client

    @property
    def name(self) -> str:
        return self._name

    def _get_client(self) -> spotipy.Spotify:
        """Lazily initialize and return authenticated Spotify client."""
        if self._client is not None:
            return self._client

        if not self._client_id or not self._client_secret:
            raise ProviderAuthenticationError(
                "Spotify credentials missing",
                "Please set SPOTIPY_CLIENT_ID and SPOTIPY_CLIENT_SECRET environment variables.",
            )

        try:
            auth_manager = SpotifyClientCredentials(
                client_id=self._client_id,
                client_secret=self._client_secret,
            )
            self._client = spotipy.Spotify(auth_manager=auth_manager)
            return self._client
        except SpotifyOauthError as e:
            logger.error("Spotify authentication error: %s", e)
            raise ProviderAuthenticationError(
                "Failed to authenticate with Spotify", str(e)
            ) from e

    @cached_search()
    def search_tracks(self, query: QueryParameters) -> list[MetadataCandidate]:
        """Search Spotify API and normalize tracks into candidates."""
        parts = []
        if query.title:
            parts.append(f"track:{query.title}")
        if query.artist:
            parts.append(f"artist:{query.artist}")
        if query.album:
            parts.append(f"album:{query.album}")
        if query.year:
            parts.append(f"year:{query.year}")
        if query.isrc:
            parts.append(f"isrc:{query.isrc}")

        if not parts:
            return []

        search_query = " ".join(parts)
        client = self._get_client()

        try:
            res = client.search(q=search_query, limit=query.limit, type="track")
            tracks_data = res.get("tracks", {}).get("items", [])
            candidates: list[MetadataCandidate] = []
            for item in tracks_data:
                candidate = self._normalize_track(item)
                if candidate:
                    candidates.append(candidate)
            return candidates
        except spotipy.SpotifyException as e:
            logger.error("Spotify API error during search: %s", e)
            raise ProviderUnavailableError("Spotify search failed", str(e)) from e
        except Exception as e:
            logger.error("Unexpected error querying Spotify: %s", e)
            raise ProviderError("Failed to query Spotify", str(e)) from e

    @cached_get_track()
    def get_track_by_id(self, track_id: str) -> MetadataCandidate | None:
        """Fetch Spotify track by track ID."""
        client = self._get_client()
        try:
            track = client.track(track_id)
            if track:
                return self._normalize_track(track)
        except Exception as e:
            logger.error("Error fetching Spotify track %s: %s", track_id, e)
            raise ProviderError("Failed to fetch track from Spotify", str(e)) from e
        return None

    def _normalize_track(self, raw: dict[str, Any]) -> MetadataCandidate | None:
        """Normalize raw Spotify track dictionary into MetadataCandidate."""
        track_id = raw.get("id")
        title = raw.get("name")
        if not track_id or not title:
            return None

        # Artists
        artists = [a.get("name", "") for a in raw.get("artists", []) if a.get("name")]
        if not artists:
            artists = ["Unknown Artist"]

        # Album & Artwork
        album_obj = raw.get("album", {})
        album_title = album_obj.get("name")
        images = album_obj.get("images", [])
        artwork_url = images[0].get("url") if images else None

        # Release date
        release_date_val: date | None = None
        year_val: int | None = None
        rel_date_str = album_obj.get("release_date")
        if rel_date_str:
            for fmt in ("%Y-%m-%d", "%Y-%m", "%Y"):
                try:
                    dt = datetime.strptime(str(rel_date_str), fmt)
                    release_date_val = dt.date()
                    year_val = dt.year
                    break
                except ValueError:
                    continue

        # Duration
        duration_ms = raw.get("duration_ms")
        duration_sec = float(duration_ms) / 1000.0 if duration_ms else None

        # ISRC
        external_ids = raw.get("external_ids", {})
        isrc_val = external_ids.get("isrc")

        return MetadataCandidate(
            provider_name="spotify",
            provider_id=track_id,
            title=title,
            artists=artists,
            album=album_title,
            album_artist=artists[0] if artists else None,
            release_date=release_date_val,
            year=year_val,
            track_number=raw.get("track_number"),
            disc_number=raw.get("disc_number"),
            isrc=isrc_val,
            duration_seconds=duration_sec,
            popularity=raw.get("popularity"),
            artwork_url=artwork_url,
            raw_payload=raw,
        )
