"""AcoustID audio fingerprinting metadata provider adapter with cross-platform binary discovery."""

from __future__ import annotations

import contextlib
import logging
import os
import platform
import shutil
import subprocess
from pathlib import Path
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


def find_fpcalc_binary() -> str | None:
    """Find the fpcalc (Chromaprint) executable across Linux, macOS, and Windows."""
    # 1. Check custom environment variable
    custom_path = os.getenv("FPCALC_PATH")
    if custom_path and Path(custom_path).is_file():
        return custom_path

    # 2. Check system PATH (respects PATHEXT on Windows)
    bin_on_path = shutil.which("fpcalc")
    if bin_on_path:
        return bin_on_path

    # 3. Check platform-specific installation paths
    system = platform.system()
    candidates: list[Path] = []

    if system == "Windows":
        local_app = os.getenv("LOCALAPPDATA")
        user_prof = os.getenv("USERPROFILE")
        prog_files = os.getenv("PROGRAMFILES", "C:\\Program Files")
        prog_files_x86 = os.getenv("PROGRAMFILES(X86)", "C:\\Program Files (x86)")

        if user_prof:
            candidates.append(Path(user_prof) / "scoop/shims/fpcalc.exe")
            candidates.append(
                Path(user_prof) / "scoop/apps/chromaprint/current/fpcalc.exe"
            )
        if local_app:
            candidates.append(Path(local_app) / "Programs/Chromaprint/fpcalc.exe")
        candidates.extend(
            [
                Path(prog_files) / "Chromaprint/fpcalc.exe",
                Path(prog_files_x86) / "Chromaprint/fpcalc.exe",
                Path("C:/tools/chromaprint/fpcalc.exe"),
                Path("C:/ProgramData/chocolatey/bin/fpcalc.exe"),
            ]
        )
    elif system == "Darwin":
        candidates.extend(
            [
                Path("/opt/homebrew/bin/fpcalc"),
                Path("/usr/local/bin/fpcalc"),
                Path("/opt/local/bin/fpcalc"),
            ]
        )
    else:  # Linux / BSD / POSIX
        with contextlib.suppress(Exception):
            home = Path.home()
            candidates.extend(
                [
                    Path("/usr/bin/fpcalc"),
                    Path("/usr/local/bin/fpcalc"),
                    Path("/snap/bin/fpcalc"),
                    home / ".local/bin/fpcalc",
                    home / "bin/fpcalc",
                ]
            )

    for p in candidates:
        if p.exists() and p.is_file():
            return str(p)

    return None


def generate_chromaprint(file_path: str) -> tuple[int, str] | None:
    """Generate (duration_seconds, fingerprint_str) using fpcalc CLI if available."""
    fpcalc_bin = find_fpcalc_binary()
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
        lines = proc.stdout.strip().splitlines()
        dur = 0
        fp = ""
        for line in lines:
            if line.startswith("DURATION="):
                dur = int(line.split("=", 1)[1])
            elif line.startswith("FINGERPRINT="):
                fp = line.split("=", 1)[1]
            elif not dur and not fp and line:
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
        use_cache: bool = True,
    ) -> None:
        load_dotenv()
        self._name = "acoustid"
        self._use_cache = use_cache
        self._client_key = client_key or os.getenv(
            "ACOUSTID_CLIENT_KEY", _DEFAULT_CLIENT_KEY
        )
        self._session = session or requests.Session()

    @property
    def name(self) -> str:
        return self._name

    @cached_search()
    def search_tracks(self, query: QueryParameters) -> list[MetadataCandidate]:
        """Search AcoustID by fingerprint or query fallback."""
        # Check if a file_path or fingerprint was passed in raw_payload
        if query.raw_payload and "fingerprint" in query.raw_payload:
            dur = int(query.raw_payload.get("duration", 0))
            fp = str(query.raw_payload.get("fingerprint", ""))
            return self.lookup_fingerprint(dur, fp)

        # Fallback to MusicBrainz lookup if title was inferred from filename
        if query.title:
            try:
                from patangoma.providers.musicbrainz import MusicBrainzProvider

                mb = MusicBrainzProvider(session=self._session)
                return mb.search_tracks(query)
            except Exception as e:
                logger.debug("AcoustID text fallback failed: %s", e)

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
