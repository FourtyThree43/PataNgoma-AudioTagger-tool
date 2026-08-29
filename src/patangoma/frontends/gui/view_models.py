"""Headless View-Models for the GUI desktop workstation."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from patangoma.application.facade import PataNgomaApplication
from patangoma.domain.models import (
    JobDescriptor,
    MetadataCandidate,
    TagPlan,
    TrackMetadata,
)


@dataclass
class LibraryViewModel:
    """View-model for library browsing, filtering, and inspection."""

    app: PataNgomaApplication
    current_directory: Path | None = None
    tracks: list[TrackMetadata] = field(default_factory=list)
    selected_index: int = -1
    filter_query: str = ""

    def load_directory(self, path: str | Path, recursive: bool = True) -> int:
        """Scan directory and populate tracks."""
        self.current_directory = Path(path)
        tracks, _summary = self.app.scan_library(path, recursive=recursive)
        self.tracks = tracks
        self.selected_index = 0 if self.tracks else -1
        return len(self.tracks)

    @property
    def selected_track(self) -> TrackMetadata | None:
        if 0 <= self.selected_index < len(self.tracks):
            return self.tracks[self.selected_index]
        return None

    @property
    def filtered_tracks(self) -> list[TrackMetadata]:
        if not self.filter_query:
            return self.tracks
        q = self.filter_query.lower()
        return [
            t
            for t in self.tracks
            if (t.title and q in t.title.lower())
            or (t.artist and q in t.artist.lower())
            or (t.album and q in t.album.lower())
        ]


@dataclass
class TagEditorViewModel:
    """View-model for track inspection, candidate matching, and tag planning."""

    app: PataNgomaApplication
    track: TrackMetadata | None = None
    candidates: list[MetadataCandidate] = field(default_factory=list)
    selected_candidate: MetadataCandidate | None = None
    active_plan: TagPlan | None = None

    def search_candidates(self, provider: str = "multi") -> list[MetadataCandidate]:
        """Fetch candidate matches for the current track."""
        if not self.track:
            return []
        cands, _title = self.app.identify_track(self.track.file_path, provider=provider)
        self.candidates = cands
        self.selected_candidate = self.candidates[0] if self.candidates else None
        return self.candidates

    def generate_plan(self) -> TagPlan | None:
        """Generate a tag plan with the currently selected candidate."""
        if not self.track or not self.selected_candidate:
            return None
        self.active_plan = self.app.create_tag_plan(
            self.track.file_path, self.selected_candidate
        )
        return self.active_plan

    def apply_plan(self, dry_run: bool = False) -> TrackMetadata | None:
        """Execute the active tag plan."""
        if not self.active_plan:
            return None
        updated = self.app.apply_tag_plan(self.active_plan, dry_run=dry_run)
        self.track = updated
        return updated


@dataclass
class JobMonitorViewModel:
    """View-model for monitoring background jobs and tasks."""

    app: PataNgomaApplication
    jobs: list[JobDescriptor] = field(default_factory=list)

    def refresh(self) -> list[JobDescriptor]:
        """Query recent jobs."""
        self.jobs = self.app.list_jobs()
        return self.jobs

    def cancel_job(self, job_id: str) -> bool:
        """Cancel a running job."""
        res = self.app.cancel_job(job_id)
        self.refresh()
        return res


@dataclass
class DiagnosticsViewModel:
    """View-model for system diagnostics and plugin health."""

    app: PataNgomaApplication
    diagnostics: dict[str, Any] = field(default_factory=dict)
    plugin_health: dict[str, dict[str, Any]] = field(default_factory=dict)

    def refresh(self) -> None:
        """Query diagnostics and plugin health."""
        self.diagnostics = self.app.run_diagnostics()
        self.plugin_health = self.app.get_plugin_health()
