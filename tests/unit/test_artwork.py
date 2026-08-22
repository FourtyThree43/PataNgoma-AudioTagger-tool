"""Unit tests for ArtworkService."""

from __future__ import annotations

import io
from pathlib import Path

from PIL import Image

from patangoma.services.artwork import ArtworkService


def _create_sample_image(
    width: int = 400, height: int = 400, color: str = "red"
) -> bytes:
    """Create a sample JPEG image in bytes."""
    buf = io.BytesIO()
    img = Image.new("RGB", (width, height), color=color)
    img.save(buf, format="JPEG")
    return buf.getvalue()


def test_artwork_validation():
    service = ArtworkService()
    img_bytes = _create_sample_image(500, 500)

    valid, mime, w, h = service.validate_image(img_bytes)
    assert valid is True
    assert mime == "image/jpeg"
    assert w == 500
    assert h == 500

    invalid, _, _, _ = service.validate_image(b"not_an_image")
    assert invalid is False


def test_artwork_resizing():
    service = ArtworkService()
    large_img = _create_sample_image(2000, 1500)

    resized = service.resize_artwork(large_img, max_width=800, max_height=800)
    valid, _, w, h = service.validate_image(resized)
    assert valid is True
    assert w <= 800
    assert h <= 800


def test_artwork_embed_and_export(mp3_empty: Path, tmp_path: Path):
    service = ArtworkService()
    sample_img = _create_sample_image(300, 300, color="blue")

    # Embed artwork
    updated = service.embed_artwork(mp3_empty, sample_img)
    assert updated.has_artwork is True

    # Export artwork
    export_path = tmp_path / "exported_cover.jpg"
    exported = service.export_artwork(mp3_empty, export_path)
    assert exported is not None
    assert exported.exists()
    assert len(exported.read_bytes()) > 0
