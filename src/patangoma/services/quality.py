"""Audio encoding quality and transcode integrity inspector."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel

from patangoma.services.audio_backend import AudioBackend


class AudioQualityReport(BaseModel):
    """Quality and encoding health report for an audio file."""

    file_path: str
    format: str
    bitrate_kbps: int | None = None
    sample_rate_hz: int | None = None
    channels: int | None = None
    duration_seconds: float | None = None
    quality_grade: (
        str  # "LOSSLESS", "HIGH_BITRATE", "MEDIUM_BITRATE", "LOW_BITRATE", "SUSPICIOUS"
    )
    issues: list[str] = []


class QualityInspector:
    """Inspects audio stream encoding parameters and flags transcode anomalies."""

    def __init__(self, backend: AudioBackend | None = None) -> None:
        self.backend = backend or AudioBackend()

    def inspect_file(self, file_path: str | Path) -> AudioQualityReport:
        """Analyze bitrates, sample rates, duration, and encoding health."""
        path = Path(file_path)
        meta = self.backend.read_metadata(str(path))

        fmt = meta.file_format.lower()
        bitrate_kbps = int(meta.bitrate / 1000) if meta.bitrate else None
        sr = meta.sample_rate
        ch = meta.channels
        dur = meta.duration_seconds

        issues: list[str] = []
        is_lossless = fmt in ("flac", "wav", "aiff", "aif", "alac")

        if is_lossless:
            grade = "LOSSLESS"
            # Flag suspicious lossless files with very low bitrates
            if bitrate_kbps and bitrate_kbps < 300:
                grade = "SUSPICIOUS"
                issues.append(
                    f"Lossless {fmt.upper()} has suspiciously low bitrate ({bitrate_kbps} kbps)"
                )
        else:
            if not bitrate_kbps:
                grade = "MEDIUM_BITRATE"
            elif bitrate_kbps >= 256:
                grade = "HIGH_BITRATE"
            elif bitrate_kbps >= 160:
                grade = "MEDIUM_BITRATE"
            else:
                grade = "LOW_BITRATE"
                issues.append(f"Low lossy bitrate ({bitrate_kbps} kbps)")

        # Short audio check
        if dur and dur < 10.0:
            issues.append(f"Very short duration ({dur:.1f}s)")

        # Monophonic check
        if ch == 1:
            issues.append("Mono audio channel")

        # Non-standard sample rate check
        if sr and sr not in (44100, 48000, 88200, 96000, 192000):
            issues.append(f"Non-standard sample rate ({sr} Hz)")

        return AudioQualityReport(
            file_path=str(path),
            format=fmt,
            bitrate_kbps=bitrate_kbps,
            sample_rate_hz=sr,
            channels=ch,
            duration_seconds=dur,
            quality_grade=grade,
            issues=issues,
        )
