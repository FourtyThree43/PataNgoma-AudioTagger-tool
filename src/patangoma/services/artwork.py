"""Artwork retrieval, validation, resizing, and embedding service."""

from __future__ import annotations

import io
import logging
from pathlib import Path

import requests
from mediafile import MediaFile
from PIL import Image

from patangoma.domain.exceptions import AudioFileNotFoundError, TagWriteError
from patangoma.domain.models import TrackMetadata
from patangoma.services.audio_backend import AudioBackend

logger = logging.getLogger(__name__)


class ArtworkService:
    """Service to handle album artwork downloading, resizing, embedding, and exporting."""

    def __init__(self, backend: AudioBackend | None = None) -> None:
        self.backend = backend or AudioBackend()

    def fetch_artwork(self, url: str, timeout: float = 10.0) -> bytes | None:
        """Download artwork bytes from an external URL."""
        if not url:
            return None
        try:
            resp = requests.get(url, timeout=timeout)
            if resp.status_code == 200 and resp.content:
                return resp.content
        except Exception as e:
            logger.warning("Failed to download artwork from %s: %s", url, e)
        return None

    def validate_image(self, image_bytes: bytes) -> tuple[bool, str | None, int, int]:
        """Validate that bytes represent a supported image format and return (valid, mime, width, height)."""
        if not image_bytes:
            return False, None, 0, 0
        try:
            with Image.open(io.BytesIO(image_bytes)) as img:
                fmt = img.format
                mime = f"image/{fmt.lower()}" if fmt else "image/jpeg"
                width, height = img.size
                return True, mime, width, height
        except Exception:
            return False, None, 0, 0

    def resize_artwork(
        self,
        image_bytes: bytes,
        max_width: int = 1000,
        max_height: int = 1000,
        quality: int = 85,
    ) -> bytes:
        """Resize image bytes to fit within max dimensions while preserving aspect ratio."""
        valid, _, width, height = self.validate_image(image_bytes)
        if not valid:
            return image_bytes

        if width <= max_width and height <= max_height:
            return image_bytes

        with Image.open(io.BytesIO(image_bytes)) as img:
            # Convert RGBA to RGB for JPEG compatibility if needed
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)

            out_buf = io.BytesIO()
            img.save(out_buf, format="JPEG", quality=quality)
            return out_buf.getvalue()

    def embed_artwork(
        self,
        file_path: str | Path,
        image_bytes: bytes,
    ) -> TrackMetadata:
        """Embed artwork image bytes directly into audio file."""
        path = Path(file_path)
        if not path.exists():
            raise AudioFileNotFoundError("Audio file not found", str(path))

        try:
            mf = MediaFile(str(path))
            mf.art = image_bytes
            mf.save()
        except Exception as e:
            raise TagWriteError(
                f"Failed to embed artwork into {path.name}", str(e)
            ) from e

        return self.backend.read_metadata(path)

    def export_artwork(
        self,
        file_path: str | Path,
        output_path: str | Path,
    ) -> Path | None:
        """Export embedded artwork to a file on disk."""
        path = Path(file_path)
        if not path.exists():
            raise AudioFileNotFoundError("Audio file not found", str(path))

        mf = MediaFile(str(path))
        art_bytes = getattr(mf, "art", None)
        if not art_bytes:
            return None

        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(art_bytes)
        return out
