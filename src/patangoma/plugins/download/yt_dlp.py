"""yt-dlp download backend plugin."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from patangoma.domain.exceptions import MediaError
from patangoma.infrastructure.subprocess.runner import ProcessRunner
from patangoma.plugins.contracts import DownloadBackendPlugin, PluginCapability


class YtDlpDownloadPlugin(DownloadBackendPlugin):
    """Download plugin powered by yt-dlp audio extraction."""

    def __init__(self, runner: ProcessRunner | None = None) -> None:
        self._runner = runner or ProcessRunner()

    @property
    def id(self) -> str:
        return "yt_dlp"

    @property
    def name(self) -> str:
        return "yt-dlp"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def capabilities(self) -> set[PluginCapability]:
        return {PluginCapability.DOWNLOAD}

    def health(self) -> dict[str, Any]:
        executable = self._runner.find_executable("yt-dlp")
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
        """Download audio stream via yt-dlp."""
        executable = self._runner.find_executable("yt-dlp")
        if not executable:
            raise MediaError("yt-dlp executable not found on system PATH")

        destination_dir.mkdir(parents=True, exist_ok=True)
        out_template = str(destination_dir / "%(title)s.%(ext)s")
        cmd = [
            str(executable),
            "-x",
            "--audio-format",
            "flac",
            "-o",
            out_template,
            url,
        ]
        res = self._runner.run(cmd, timeout_seconds=300.0)
        if not res.is_success:
            raise MediaError(f"yt-dlp extraction failed: {res.stderr}")

        return destination_dir
