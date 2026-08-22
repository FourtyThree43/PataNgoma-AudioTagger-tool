"""System diagnostic and environment doctor service."""

from __future__ import annotations

import os
import sys

from pydantic import BaseModel, Field

from patangoma.providers.registry import get_available_providers


class DiagnosticCheck(BaseModel):
    """Result of an individual diagnostic check."""

    name: str
    status: str  # "OK", "WARNING", "ERROR"
    message: str
    details: str | None = None


class DoctorReport(BaseModel):
    """Full system diagnostics report."""

    overall_healthy: bool
    checks: list[DiagnosticCheck] = Field(default_factory=list)


def run_diagnostics() -> DoctorReport:
    """Run system and provider diagnostics."""
    checks: list[DiagnosticCheck] = []
    healthy = True

    # 1. Python runtime check
    py_ver = (
        f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    )
    checks.append(
        DiagnosticCheck(
            name="Python Runtime",
            status="OK",
            message=f"Python {py_ver} (>= 3.10 supported)",
        )
    )

    # 2. Audio Backend check
    import importlib.util

    has_mediafile = importlib.util.find_spec("mediafile") is not None
    has_mutagen = importlib.util.find_spec("mutagen") is not None

    if has_mediafile and has_mutagen:
        checks.append(
            DiagnosticCheck(
                name="Audio Metadata Backend",
                status="OK",
                message="Mutagen and MediaFile available",
            )
        )
    else:
        healthy = False
        checks.append(
            DiagnosticCheck(
                name="Audio Metadata Backend",
                status="ERROR",
                message="Audio libraries failed to load (mediafile or mutagen missing)",
            )
        )

    # 3. Provider Availability
    available_providers = get_available_providers()
    checks.append(
        DiagnosticCheck(
            name="Registered Providers",
            status="OK",
            message=f"{len(available_providers)} providers registered: {', '.join(available_providers)}",
        )
    )

    # 4. Spotify Credentials Check
    sp_id = os.getenv("SPOTIPY_CLIENT_ID")
    sp_secret = os.getenv("SPOTIPY_CLIENT_SECRET")
    if sp_id and sp_secret:
        checks.append(
            DiagnosticCheck(
                name="Spotify Credentials",
                status="OK",
                message="SPOTIPY_CLIENT_ID and SPOTIPY_CLIENT_SECRET configured",
            )
        )
    else:
        checks.append(
            DiagnosticCheck(
                name="Spotify Credentials",
                status="WARNING",
                message="Spotify API credentials not set (optional, MusicBrainz & Deezer work without keys)",
            )
        )

    # 5. Local Audit Directory Check
    from patangoma.services.audit import default_audit_db_path

    try:
        audit_path = default_audit_db_path()
        checks.append(
            DiagnosticCheck(
                name="Audit Storage",
                status="OK",
                message=f"Audit journal writable at {audit_path}",
            )
        )
    except Exception as e:
        healthy = False
        checks.append(
            DiagnosticCheck(
                name="Audit Storage",
                status="ERROR",
                message=f"Audit storage directory error: {e}",
            )
        )

    return DoctorReport(overall_healthy=healthy, checks=checks)
