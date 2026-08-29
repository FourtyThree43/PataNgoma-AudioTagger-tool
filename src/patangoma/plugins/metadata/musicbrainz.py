"""MusicBrainz metadata provider plugin."""

from __future__ import annotations

import logging
from datetime import date, datetime
from typing import Any

import musicbrainzngs as mb

from patangoma.domain.exceptions import ProviderError, ProviderUnavailableError
from patangoma.domain.models import MetadataCandidate, QueryParameters
from patangoma.plugins.contracts import MetadataProviderPlugin, PluginCapability
from patangoma.providers.base import BaseMetadataProvider
from patangoma.providers.cache import cached_get_track, cached_search

logger = logging.getLogger(__name__)


class MusicBrainzPlugin(BaseMetadataProvider, MetadataProviderPlugin):
    """Metadata provider plugin backed by MusicBrainz API."""

    def __init__(
        self,
        app_name: str = "PataNgoma",
        app_version: str = "1.0.0",
        contact: str = "patangoma@example.com",
    ) -> None:
        self._name = "musicbrainz"
        mb.set_useragent(app_name, app_version, contact)
        mb.set_format("json")

    @property
    def name(self) -> str:
        return self._name

    @property
    def capabilities(self) -> set[PluginCapability]:
        return {PluginCapability.METADATA}

    @cached_search()
    def search_tracks(self, query: QueryParameters) -> list[MetadataCandidate]:
        """Search recordings on MusicBrainz and normalize into MetadataCandidate objects."""
        query_params: dict[str, Any] = {}
        if query.title:
            query_params["recording"] = query.title
        if query.artist:
            query_params["artist"] = query.artist
        if query.album:
            query_params["release"] = query.album
        if query.isrc:
            query_params["isrc"] = query.isrc

        if not query_params:
            return []

        try:
            res = mb.search_recordings(**query_params, limit=query.limit)
        except mb.WebServiceError as e:
            logger.error("MusicBrainz WebService error: %s", e)
            raise ProviderUnavailableError(
                "MusicBrainz API request failed", str(e)
            ) from e
        except Exception as e:
            logger.error("Unexpected error searching MusicBrainz: %s", e)
            raise ProviderError("Failed to search MusicBrainz", str(e)) from e

        recordings = res.get("recording-list", [])
        candidates: list[MetadataCandidate] = []
        for rec in recordings:
            candidate = self._normalize_recording(rec)
            if candidate:
                candidates.append(candidate)

        return candidates

    @cached_get_track()
    def get_track_by_id(self, track_id: str) -> MetadataCandidate | None:
        """Fetch recording by MusicBrainz recording ID (mb_trackid)."""
        try:
            res = mb.get_recording_by_id(
                track_id,
                includes=["artists", "releases", "isrcs", "media"],
            )
            recording = res.get("recording")
            if recording:
                return self._normalize_recording(recording)
        except mb.WebServiceError as e:
            logger.error("MusicBrainz WebService error fetching ID %s: %s", track_id, e)
            raise ProviderUnavailableError(
                "MusicBrainz API fetch failed", str(e)
            ) from e
        except Exception as e:
            logger.error("Error fetching MusicBrainz ID %s: %s", track_id, e)
            raise ProviderError("Failed to fetch from MusicBrainz", str(e)) from e

        return None

    def _normalize_recording(self, rec: dict[str, Any]) -> MetadataCandidate | None:
        """Normalize raw MusicBrainz recording dictionary into MetadataCandidate."""
        rec_id = rec.get("id")
        title = rec.get("title")
        if not rec_id or not title:
            return None

        # Extract artists
        artists: list[str] = []
        artist_id: str | None = None
        for credit in rec.get("artist-credit", []):
            if isinstance(credit, dict):
                art = credit.get("artist", {})
                if "name" in art:
                    artists.append(art["name"])
                if not artist_id and "id" in art:
                    artist_id = art["id"]
            elif isinstance(credit, str):
                pass

        if not artists and "artist-credit-phrase" in rec:
            artists.append(rec["artist-credit-phrase"])

        # Extract release info
        album_name: str | None = None
        album_id: str | None = None
        album_artist: str | None = None
        release_date_val: date | None = None
        year_val: int | None = None
        track_num: int | None = None
        track_tot: int | None = None
        disc_num: int | None = None
        artwork_url: str | None = None

        releases = rec.get("release-list", [])
        if releases:
            rel = releases[0]
            album_name = rel.get("title")
            album_id = rel.get("id")

            # Album artist
            rel_artists = rel.get("artist-credit", [])
            if rel_artists and isinstance(rel_artists[0], dict):
                album_artist = rel_artists[0].get("artist", {}).get("name")

            # Date parsing
            date_str = rel.get("date")
            if date_str:
                for fmt in ("%Y-%m-%d", "%Y-%m", "%Y"):
                    try:
                        dt = datetime.strptime(str(date_str), fmt)
                        release_date_val = dt.date()
                        year_val = dt.year
                        break
                    except ValueError:
                        continue

            # Medium & Track numbers
            mediums = rel.get("medium-list", [])
            if mediums:
                med = mediums[0]
                disc_num = med.get("position")
                track_tot = med.get("track-count") or med.get("track-list-count")
                tracks = med.get("track-list", [])
                if tracks:
                    track_obj = tracks[0]
                    try:
                        track_num = int(track_obj.get("number", 0)) or track_obj.get(
                            "position"
                        )
                    except (ValueError, TypeError):
                        track_num = track_obj.get("position")

        # Duration
        length_ms = rec.get("length")
        duration_sec = float(length_ms) / 1000.0 if length_ms else None

        # ISRC
        isrc_list = rec.get("isrc-list", [])
        isrc_val = isrc_list[0] if isrc_list else None

        # Artwork link
        if album_id:
            artwork_url = f"https://coverartarchive.org/release/{album_id}/front-500"

        return MetadataCandidate(
            provider_name="musicbrainz",
            provider_id=rec_id,
            title=title,
            artists=artists if artists else ["Unknown Artist"],
            album=album_name,
            album_artist=album_artist,
            release_date=release_date_val,
            year=year_val,
            track_number=track_num,
            track_total=track_tot,
            disc_number=disc_num,
            isrc=isrc_val,
            duration_seconds=duration_sec,
            artwork_url=artwork_url,
            mb_trackid=rec_id,
            mb_artistid=artist_id,
            mb_albumid=album_id,
            raw_payload=rec,
        )


# Backward compatibility alias
MusicBrainzProvider = MusicBrainzPlugin
