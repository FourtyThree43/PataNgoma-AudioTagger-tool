"""Subprocess runner for external tools (fpcalc, ffmpeg, ffprobe, aria2c, yt-dlp)."""

from __future__ import annotations

import os
import shutil
import subprocess
import time
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from patangoma.domain.exceptions import MediaError


@dataclass(frozen=True)
class ProcessResult:
    """Outcome of an external process execution."""

    exit_code: int
    stdout: str
    stderr: str
    command: list[str]
    duration_seconds: float

    @property
    def is_success(self) -> bool:
        return self.exit_code == 0


class ProcessRunner:
    """Safe runner for external command execution with timeout and process lifecycle control."""

    @staticmethod
    def find_executable(
        name: str, extra_paths: Sequence[str | Path] = ()
    ) -> Path | None:
        """Find an executable by name across system PATH and custom search paths."""
        found = shutil.which(name)
        if found:
            return Path(found)

        for candidate_dir in extra_paths:
            p = Path(candidate_dir) / name
            if p.is_file() and os.access(p, os.X_OK):
                return p
        return None

    def run(
        self,
        cmd: Sequence[str],
        timeout_seconds: float = 60.0,
        cwd: str | Path | None = None,
        env: dict[str, str] | None = None,
    ) -> ProcessResult:
        """Execute command safely and capture output and execution time."""
        cmd_list = list(cmd)
        if not cmd_list:
            raise MediaError("Cannot execute empty command list")

        start_time = time.monotonic()
        try:
            res = subprocess.run(
                cmd_list,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                cwd=str(cwd) if cwd else None,
                env=env,
                check=False,
            )
            duration = time.monotonic() - start_time
            return ProcessResult(
                exit_code=res.returncode,
                stdout=res.stdout,
                stderr=res.stderr,
                command=cmd_list,
                duration_seconds=duration,
            )
        except subprocess.TimeoutExpired as e:
            duration = time.monotonic() - start_time
            stdout_text = (
                e.stdout.decode("utf-8", errors="replace")
                if isinstance(e.stdout, bytes)
                else (e.stdout or "")
            )
            stderr_text = (
                e.stderr.decode("utf-8", errors="replace")
                if isinstance(e.stderr, bytes)
                else (e.stderr or "")
            )
            return ProcessResult(
                exit_code=-1,
                stdout=stdout_text,
                stderr=f"Command timed out after {timeout_seconds}s: {stderr_text}",
                command=cmd_list,
                duration_seconds=duration,
            )
        except Exception as e:
            duration = time.monotonic() - start_time
            return ProcessResult(
                exit_code=-1,
                stdout="",
                stderr=str(e),
                command=cmd_list,
                duration_seconds=duration,
            )
