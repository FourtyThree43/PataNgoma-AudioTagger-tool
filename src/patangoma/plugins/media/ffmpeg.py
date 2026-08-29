"""FFmpeg media tool plugin."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from patangoma.domain.exceptions import MediaError
from patangoma.infrastructure.subprocess.runner import ProcessRunner
from patangoma.plugins.contracts import MediaToolPlugin, PluginCapability


class FFmpegMediaPlugin(MediaToolPlugin):
    """Media plugin providing audio transcoding and media probing via ffmpeg."""

    def __init__(self, runner: ProcessRunner | None = None) -> None:
        self._runner = runner or ProcessRunner()

    @property
    def id(self) -> str:
        return "ffmpeg"

    @property
    def name(self) -> str:
        return "FFmpeg"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def capabilities(self) -> set[PluginCapability]:
        return {PluginCapability.MEDIA_TOOL}

    def is_available(self) -> bool:
        return self._runner.find_executable("ffmpeg") is not None

    def health(self) -> dict[str, Any]:
        executable = self._runner.find_executable("ffmpeg")
        return {
            "status": "HEALTHY" if executable else "WARNING",
            "available": executable is not None,
            "executable": str(executable) if executable else None,
        }

    def initialize(self) -> None:
        pass

    def shutdown(self) -> None:
        pass

    def transcode(
        self,
        input_path: Path,
        output_path: Path,
        codec: str = "flac",
    ) -> Path:
        """Transcode audio file to target output using ffmpeg."""
        executable = self._runner.find_executable("ffmpeg")
        if not executable:
            raise MediaError("ffmpeg executable not found on system PATH")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        cmd = [
            str(executable),
            "-y",
            "-i",
            str(input_path),
            "-c:a",
            codec,
            str(output_path),
        ]
        res = self._runner.run(cmd, timeout_seconds=120.0)
        if not res.is_success:
            raise MediaError(f"FFmpeg transcoding failed: {res.stderr}")

        return output_path
