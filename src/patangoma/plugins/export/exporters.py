"""Export plugins for track metadata and playlists."""

from __future__ import annotations

import csv
import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from patangoma.domain.models import TrackMetadata
from patangoma.plugins.contracts import ExporterPlugin, PluginCapability


class JSONExporterPlugin(ExporterPlugin):
    """Exports catalog of tracks to JSON."""

    @property
    def id(self) -> str:
        return "export_json"

    @property
    def name(self) -> str:
        return "JSON Exporter"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def format_name(self) -> str:
        return "json"

    @property
    def capabilities(self) -> set[PluginCapability]:
        return {PluginCapability.EXPORTER}

    def health(self) -> dict[str, Any]:
        return {"status": "HEALTHY", "format": self.format_name}

    def initialize(self) -> None:
        pass

    def shutdown(self) -> None:
        pass

    def export_tracks(self, tracks: Sequence[TrackMetadata], output_path: Path) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        data = [t.model_dump(mode="json") for t in tracks]
        output_path.write_text(
            json.dumps(data, indent=2, default=str), encoding="utf-8"
        )
        return output_path


class CSVExporterPlugin(ExporterPlugin):
    """Exports catalog of tracks to CSV spreadsheet format."""

    @property
    def id(self) -> str:
        return "export_csv"

    @property
    def name(self) -> str:
        return "CSV Exporter"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def format_name(self) -> str:
        return "csv"

    @property
    def capabilities(self) -> set[PluginCapability]:
        return {PluginCapability.EXPORTER}

    def health(self) -> dict[str, Any]:
        return {"status": "HEALTHY", "format": self.format_name}

    def initialize(self) -> None:
        pass

    def shutdown(self) -> None:
        pass

    def export_tracks(self, tracks: Sequence[TrackMetadata], output_path: Path) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        fields = [
            "file_path",
            "title",
            "artist",
            "album",
            "year",
            "track_number",
            "genre",
            "duration_seconds",
            "bitrate",
        ]
        with output_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
            writer.writeheader()
            for t in tracks:
                writer.writerow(t.model_dump(mode="json"))
        return output_path


class M3UPlaylistExporterPlugin(ExporterPlugin):
    """Exports tracks to M3U / M3U8 playlist."""

    @property
    def id(self) -> str:
        return "export_m3u"

    @property
    def name(self) -> str:
        return "M3U Playlist Exporter"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def format_name(self) -> str:
        return "m3u"

    @property
    def capabilities(self) -> set[PluginCapability]:
        return {PluginCapability.EXPORTER}

    def health(self) -> dict[str, Any]:
        return {"status": "HEALTHY", "format": self.format_name}

    def initialize(self) -> None:
        pass

    def shutdown(self) -> None:
        pass

    def export_tracks(self, tracks: Sequence[TrackMetadata], output_path: Path) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        lines = ["#EXTM3U"]
        for t in tracks:
            dur = int(t.duration_seconds or 0)
            artist = t.artist or "Unknown Artist"
            title = t.title or "Unknown Title"
            lines.append(f"#EXTINF:{dur},{artist} - {title}")
            lines.append(str(t.file_path))
        output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return output_path
