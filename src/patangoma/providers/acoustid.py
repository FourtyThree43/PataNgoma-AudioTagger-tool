"""AcoustID audio fingerprinting metadata provider adapter."""

from __future__ import annotations

import contextlib
import logging
import os
import shutil
import subprocess
from typing import Any

import requests
from dotenv import load_dotenv

from patangoma.domain.exceptions import ProviderError, ProviderUnavailableError
from patangoma.domain.models import MetadataCandidate, QueryParameters
from patangoma.providers.base import MetadataProvider
from patangoma.providers.cache import cached_get_track, cached_search

logger = logging.getLogger(__name__)

_ACOUSTID_LOOKUP_URL = "https://api.acoustid.org/v2/lookup"
# Default public application client ID for AcoustID lookups
_DEFAULT_CLIENT_KEY = "8XaBELgH"


def generate_chromaprint(file_path: str) -> tuple[int, str] | None:
    """Generate (duration_seconds, fingerprint_str) using fpcalc CLI if available."""
    fpcalc_bin = shutil.which("fpcalc")
    if not fpcalc_bin:
        return None

    try:
        proc = subprocess.run(
            [fpcalc_bin, "-plain", file_path],
            capture_output=True,
            text=True,
            check=True,
            timeout=15.0,
        )
        # fpcalc output with -plain:
        # DURATION=234
        # FINGERPRINT=AQADtHKUaUkSRd...
        lines = proc.stdout.strip().splitlines()
        dur = 0
        fp = ""
        for line in lines:
            if line.startswith("DURATION="):
                dur = int(line.split("=", 1)[1])
            elif line.startswith("FINGERPRINT="):
                fp = line.split("=", 1)[1]
            elif not dur and not fp and line:
                # Raw plain fingerprint
                fp = line.strip()
        if fp:
            return dur, fp
    except Exception as e:
        logger.debug("Failed to calculate chromaprint for %s: %s", file_path, e)
    return None


class AcoustIDProvider(MetadataProvider):
    """Metadata provider backed by AcoustID fingerprint lookup API."""

    def __init__(
        self,
        client_key: str | None = None,
        session: requests.Session | None = None,
    ) -> None:
        load_dotenv()
        self._name = "acoustid"
        self._client_key = client_key or os.getenv(
            "ACOUSTID_CLIENT_KEY", _DEFAULT_CLIENT_KEY
        )
        self._session = session or requests.Session()

    @property
    def name(self) -> str:
        return self._name

    @cached_search()
    def search_tracks(self, query: QueryParameters) -> list[MetadataCandidate]:
        """Search AcoustID by fingerprint or query."""
        # AcoustID search primarily requires duration + fingerprint from raw_payload or query
        return []

    def lookup_fingerprint(
        self, duration_seconds: int, fingerprint: str
    ) -> list[MetadataCandidate]:
        """Lookup metadata candidates directly using an acoustic fingerprint."""
        if not fingerprint:
            return []

        params = {
            "client": self._client_key,
            "meta": "recordings releasegroups releases tracks compress",
            "duration": str(duration_seconds),
            "fingerprint": fingerprint,
        }

        try:
            resp = self._session.get(_ACOUSTID_LOOKUP_URL, params=params, timeout=10.0)
            resp.raise_for_status()
            data = resp.json()
        except requests.RequestException as e:
            logger.error("AcoustID API lookup failed: %s", e)
            raise ProviderUnavailableError("AcoustID request failed", str(e)) from e
        except Exception as e:
            logger.error("Error parsing AcoustID response: %s", e)
            raise ProviderError("Failed to parse AcoustID response", str(e)) from e

        if data.get("status") != "ok":
            error_msg = data.get("error", {}).get("message", "AcoustID lookup failed")
            raise ProviderError(f"AcoustID API error: {error_msg}")

        candidates: list[MetadataCandidate] = []
        results = data.get("results", [])
        for res in results:
            score = float(res.get("score", 0.0))
            recordings = res.get("recordings", [])
            for rec in recordings:
                cand = self._normalize_recording(rec, score=score)
                if cand:
                    candidates.append(cand)

        return candidates

    @cached_get_track()
    def get_track_by_id(self, track_id: str) -> MetadataCandidate | None:
        """Fetch candidate by AcoustID result ID or MusicBrainz ID."""
        # AcoustID lookup by MBID is handled via MusicBrainz provider
        return None

    def _normalize_recording(
        self, rec: dict[str, Any], score: float = 1.0
    ) -> MetadataCandidate | None:
        """Normalize AcoustID recording object into a standard MetadataCandidate."""
        rec_id = rec.get("id")
        title = rec.get("title")
        if not rec_id or not title:
            return None

        # Artists
        artists: list[str] = []
        artist_id = None
        for a in rec.get("artists", []):
            name = a.get("name")
            if name:
                artists.append(name)
            if not artist_id and a.get("id"):
                artist_id = a.get("id")

        primary_artist = artists[0] if artists else "Unknown Artist"

        # Release / Album info
        album_name = None
        album_id = None
        year = None
        releases = rec.get("releases", [])
        if releases:
            rel = releases[0]
            album_name = rel.get("title")
            album_id = rel.get("id")
            if rel.get("date"):
                date_dict = rel.get("date")
                if isinstance(date_dict, dict):
                    year = date_dict.get("year")
                elif isinstance(date_dict, str) and len(date_dict) >= 4:
                    with contextlib.suppress(ValueError):
                        year = int(date_dict[:4])

        dur_sec = float(rec.get("duration", 0)) or None

        return MetadataCandidate(
            provider_name="acoustid",
            provider_id=str(rec_id),
            title=title,
            artists=artists if artists else [primary_artist],
            album=album_name,
            album_artist=primary_artist,
            year=year,
            duration_seconds=dur_sec,
            popularity=int(score * 100),
            mb_trackid=rec_id,
            mb_artistid=artist_id,
            mb_albumid=album_id,
            raw_payload=rec,
        )
