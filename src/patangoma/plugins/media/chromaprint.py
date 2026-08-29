"""Chromaprint fpcalc media tool plugin."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from patangoma.infrastructure.subprocess.runner import ProcessRunner
from patangoma.plugins.contracts import MediaToolPlugin, PluginCapability
from patangoma.plugins.metadata.acoustid import find_fpcalc_binary, generate_chromaprint


class ChromaprintMediaPlugin(MediaToolPlugin):
    """Media plugin providing acoustic fingerprint computation using fpcalc."""

    def __init__(self, runner: ProcessRunner | None = None) -> None:
        self._runner = runner or ProcessRunner()

    @property
    def id(self) -> str:
        return "chromaprint"

    @property
    def name(self) -> str:
        return "Chromaprint fpcalc"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def capabilities(self) -> set[PluginCapability]:
        return {PluginCapability.MEDIA_TOOL}

    def is_available(self) -> bool:
        return find_fpcalc_binary() is not None

    def health(self) -> dict[str, Any]:
        bin_path = find_fpcalc_binary()
        return {
            "status": "HEALTHY" if bin_path else "WARNING",
            "available": bin_path is not None,
            "executable": bin_path,
        }

    def initialize(self) -> None:
        pass

    def shutdown(self) -> None:
        pass

    def fingerprint(self, file_path: str | Path) -> tuple[int, str] | None:
        """Calculate duration and acoustic fingerprint for an audio file."""
        return generate_chromaprint(str(file_path))
