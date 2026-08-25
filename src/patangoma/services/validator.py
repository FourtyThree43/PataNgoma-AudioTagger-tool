"""File header, magic-bytes, and audio corruption validator."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel

_MAGIC_HEADERS: dict[str, list[bytes]] = {
    "flac": [b"fLaC"],
    "mp3": [b"ID3", b"\xff\xfb", b"\xff\xfa", b"\xff\xf3", b"\xff\xf2"],
    "wav": [b"RIFF"],
    "ogg": [b"OggS"],
    "opus": [b"OggS"],
    "oga": [b"OggS"],
    "m4a": [b"\x00\x00\x00\x18ftypM4A", b"\x00\x00\x00\x20ftypM4A", b"ftyp"],
    "mp4": [b"ftyp"],
    "m4b": [b"ftyp"],
    "aac": [b"ID3", b"\xff\xf1", b"\xff\xf9"],
    "wma": [b"\x30\x26\xb2\x75\x8e\x66\xcf\x11"],
    "aiff": [b"FORM"],
    "aif": [b"FORM"],
    "alac": [b"ftyp"],
}


class FileIntegrityReport(BaseModel):
    """Integrity check report for an audio file."""

    file_path: str
    file_size_bytes: int = 0
    detected_format: str = "unknown"
    header_valid: bool = False
    is_readable: bool = False
    error_message: str | None = None


class FileValidator:
    """Pre-flight file integrity and magic byte inspector."""

    @staticmethod
    def validate_file(file_path: str | Path) -> FileIntegrityReport:
        """Inspect file magic bytes and verify audio file readability."""
        path = Path(file_path)
        if not path.exists():
            return FileIntegrityReport(
                file_path=str(path),
                error_message="File does not exist",
            )

        if not path.is_file():
            return FileIntegrityReport(
                file_path=str(path),
                error_message="Path is not a regular file",
            )

        size = path.stat().st_size
        if size == 0:
            return FileIntegrityReport(
                file_path=str(path),
                file_size_bytes=0,
                error_message="File is 0 bytes (empty)",
            )

        ext = path.suffix.lower().lstrip(".")
        detected_fmt = ext or "unknown"

        # Read first 64 bytes for magic header check
        header_valid = False
        try:
            with path.open("rb") as f:
                header = f.read(64)

            # Check known magic signatures
            if ext in _MAGIC_HEADERS:
                for sig in _MAGIC_HEADERS[ext]:
                    if sig in header:
                        header_valid = True
                        break
            else:
                # Any recognized audio header
                for fmt, sigs in _MAGIC_HEADERS.items():
                    for sig in sigs:
                        if sig in header:
                            header_valid = True
                            detected_fmt = fmt
                            break
                    if header_valid:
                        break

            # If header didn't match known signatures, flag as potentially corrupt
            if not header_valid:
                return FileIntegrityReport(
                    file_path=str(path),
                    file_size_bytes=size,
                    detected_format=detected_fmt,
                    header_valid=False,
                    is_readable=False,
                    error_message=f"Invalid or corrupt audio file header for format .{ext}",
                )

            return FileIntegrityReport(
                file_path=str(path),
                file_size_bytes=size,
                detected_format=detected_fmt,
                header_valid=True,
                is_readable=True,
            )

        except Exception as e:
            return FileIntegrityReport(
                file_path=str(path),
                file_size_bytes=size,
                detected_format=detected_fmt,
                header_valid=False,
                is_readable=False,
                error_message=f"Filesystem read error: {e}",
            )
