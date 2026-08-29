"""TUI Screen components and widgets for the Textual Workstation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from patangoma.application.facade import PataNgomaApplication
from patangoma.domain.models import MetadataCandidate, TagPlan, TrackMetadata


class TUIScreenModel:
    """Headless state and controller logic for TUI screens."""

    def __init__(self, app: PataNgomaApplication) -> None:
        self.app = app
        self.current_directory: Path | None = None
        self.tracks: list[TrackMetadata] = []
        self.selected_track: TrackMetadata | None = None
        self.candidates: list[MetadataCandidate] = []
        self.active_plan: TagPlan | None = None

    def scan_directory(self, path: str | Path) -> int:
        """Scan a directory and populate local track buffer."""
        self.current_directory = Path(path)
        tracks, _summary = self.app.scan_library(path, recursive=True)
        self.tracks = tracks
        if self.tracks:
            self.selected_track = self.tracks[0]
        return len(self.tracks)

    def select_track(self, index: int) -> TrackMetadata | None:
        """Select a track by index."""
        if 0 <= index < len(self.tracks):
            self.selected_track = self.tracks[index]
            self.candidates = []
            self.active_plan = None
            return self.selected_track
        return None

    def search_candidates(self, provider: str = "multi") -> list[MetadataCandidate]:
        """Search candidate matches for selected track."""
        if not self.selected_track:
            return []
        cands, _title = self.app.identify_track(
            self.selected_track.file_path, provider=provider
        )
        self.candidates = cands
        return self.candidates

    def plan_candidate(self, candidate: MetadataCandidate) -> TagPlan | None:
        """Generate a tag plan for the selected track and candidate."""
        if not self.selected_track:
            return None
        self.active_plan = self.app.create_tag_plan(
            self.selected_track.file_path, candidate
        )
        return self.active_plan

    def apply_plan(self, dry_run: bool = False) -> TrackMetadata | None:
        """Apply active tag plan."""
        if not self.active_plan:
            return None
        updated = self.app.apply_tag_plan(self.active_plan, dry_run=dry_run)
        self.selected_track = updated
        return updated

    def get_diagnostics(self) -> dict[str, Any]:
        """Run system diagnostics."""
        return {
            "doctor": self.app.run_diagnostics(),
            "plugins": self.app.get_plugin_health(),
        }

    def get_jobs(self) -> list[Any]:
        """Query active and recent background jobs."""
        return self.app.list_jobs()

    def get_audit_history(self, limit: int = 50) -> list[Any]:
        """Query audit log records."""
        path_filter = (
            str(self.selected_track.file_path) if self.selected_track else None
        )
        return self.app.get_audit_history(file_path=path_filter, limit=limit)
