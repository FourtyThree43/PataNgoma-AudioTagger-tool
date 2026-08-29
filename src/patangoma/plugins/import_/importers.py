"""Import plugins for track metadata."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from patangoma.domain.models import TrackMetadata
from patangoma.plugins.contracts import ImporterPlugin, PluginCapability


class JSONImporterPlugin(ImporterPlugin):
    """Imports track metadata from exported JSON files."""

    @property
    def id(self) -> str:
        return "import_json"

    @property
    def name(self) -> str:
        return "JSON Importer"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def format_name(self) -> str:
        return "json"

    @property
    def capabilities(self) -> set[PluginCapability]:
        return {PluginCapability.IMPORTER}

    def health(self) -> dict[str, Any]:
        return {"status": "HEALTHY", "format": self.format_name}

    def initialize(self) -> None:
        pass

    def shutdown(self) -> None:
        pass

    def import_tracks(self, input_path: Path) -> list[TrackMetadata]:
        text = input_path.read_text(encoding="utf-8")
        data = json.loads(text)
        if isinstance(data, list):
            return [TrackMetadata.model_validate(item) for item in data]
        if isinstance(data, dict):
            return [TrackMetadata.model_validate(data)]
        return []
