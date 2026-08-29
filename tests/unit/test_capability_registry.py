"""Unit tests for CapabilityRegistry and all capability plugin families."""

from __future__ import annotations

from pathlib import Path

from patangoma.domain.models import TrackMetadata
from patangoma.plugins.contracts import PluginCapability
from patangoma.plugins.discovery import create_default_plugin_registry


def test_capability_registry_queries():
    """Verify CapabilityRegistry provides typed access across all capabilities."""
    reg = create_default_plugin_registry()
    cap = reg.capabilities

    # 1. Metadata Providers
    meta_provs = cap.list_metadata_providers()
    assert len(meta_provs) == 7
    mb = cap.get_metadata_provider("musicbrainz")
    assert mb is not None
    assert mb.name == "musicbrainz"

    # 2. Download Backends
    dl_backends = cap.list_download_backends()
    assert len(dl_backends) == 2
    aria = cap.get_download_backend("aria2")
    assert aria is not None
    assert PluginCapability.DOWNLOAD in aria.capabilities

    # 3. Media Tools
    media_tools = cap.list_media_tools()
    assert len(media_tools) == 2
    ffmpeg = cap.get_media_tool("ffmpeg")
    assert ffmpeg is not None
    chroma = cap.get_media_tool("chromaprint")
    assert chroma is not None

    # 4. Artwork Providers
    art_provs = cap.list_artwork_providers()
    assert len(art_provs) == 1
    assert art_provs[0].id == "coverartarchive"

    # 5. Exporters & Importers
    exporters = cap.list_exporters()
    assert len(exporters) == 3
    json_exp = cap.get_exporter("json")
    assert json_exp is not None
    csv_exp = cap.get_exporter("csv")
    assert csv_exp is not None
    m3u_exp = cap.get_exporter("m3u")
    assert m3u_exp is not None

    importers = cap.list_importers()
    assert len(importers) == 1
    json_imp = cap.get_importer("json")
    assert json_imp is not None


def test_export_and_import_plugins_roundtrip(tmp_path: Path):
    """Test exporting tracks to JSON and importing back."""
    reg = create_default_plugin_registry()
    cap = reg.capabilities

    json_exp = cap.get_exporter("json")
    json_imp = cap.get_importer("json")
    assert json_exp is not None and json_imp is not None

    tracks = [
        TrackMetadata(
            file_path=str(tmp_path / "song.mp3"),
            title="Plugin Track",
            artist="Plugin Artist",
            album="Plugin Album",
            year=2025,
        )
    ]

    out_file = tmp_path / "catalog.json"
    exported_path = json_exp.export_tracks(tracks, out_file)
    assert exported_path.exists()

    imported = json_imp.import_tracks(exported_path)
    assert len(imported) == 1
    assert imported[0].title == "Plugin Track"
    assert imported[0].artist == "Plugin Artist"
