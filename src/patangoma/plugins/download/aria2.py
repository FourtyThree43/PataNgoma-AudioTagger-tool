"""Aria2 download backend plugin."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from patangoma.domain.exceptions import MediaError
from patangoma.infrastructure.subprocess.runner import ProcessRunner
from patangoma.plugins.contracts import DownloadBackendPlugin, PluginCapability


class Aria2DownloadPlugin(DownloadBackendPlugin):
    """Download plugin powered by aria2c multi-connection downloader."""

    def __init__(self, runner: ProcessRunner | None = None) -> None:
        self._runner = runner or ProcessRunner()

    @property
    def id(self) -> str:
        return "aria2"

    @property
    def name(self) -> str:
        return "aria2"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def capabilities(self) -> set[PluginCapability]:
        return {PluginCapability.DOWNLOAD}

    def health(self) -> dict[str, Any]:
        executable = self._runner.find_executable("aria2c")
        return {
            "status": "HEALTHY" if executable else "WARNING",
            "available": executable is not None,
            "executable": str(executable) if executable else None,
        }

    def initialize(self) -> None:
        pass

    def shutdown(self) -> None:
        pass

    def download(
        self,
        url: str,
        destination_dir: Path,
        options: dict[str, Any] | None = None,
    ) -> Path:
        """Download media URL to destination using aria2c."""
        executable = self._runner.find_executable("aria2c")
        if not executable:
            raise MediaError("aria2c executable not found on system PATH")

        destination_dir.mkdir(parents=True, exist_ok=True)
        cmd = [str(executable), "--dir", str(destination_dir), url]
        res = self._runner.run(cmd, timeout_seconds=300.0)
        if not res.is_success:
            raise MediaError(f"aria2 download failed: {res.stderr}")

        return destination_dir
