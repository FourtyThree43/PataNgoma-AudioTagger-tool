"""Unified Application Platform Facade for PataNgoma."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Any

from patangoma.application.events.bus import EventBus
from patangoma.application.jobs.manager import JobManager
from patangoma.domain.models import (
    AuditRecord,
    ConfidenceLevel,
    JobDescriptor,
    MetadataCandidate,
    QueryParameters,
    TagPlan,
    TrackMetadata,
)
from patangoma.infrastructure.configuration.manager import ConfigurationManager
from patangoma.infrastructure.media.backend import (
    AudioBackendPort,
    MediaFileAudioBackend,
)
from patangoma.matching.matcher import MatchingEngine
from patangoma.plugins.contracts import Plugin
from patangoma.plugins.discovery import create_default_plugin_registry
from patangoma.plugins.registry import PluginRegistry
from patangoma.services.aggregator import MetadataAggregator
from patangoma.services.ai_reasoner import MetadataReasoner
from patangoma.services.artwork import ArtworkService
from patangoma.services.audit import AuditJournal
from patangoma.services.batch import BatchService
from patangoma.services.doctor import run_diagnostics
from patangoma.services.duplicates import DuplicateDetector
from patangoma.services.genre import GenreNormalizer
from patangoma.services.planner import PlanEngine
from patangoma.services.playlist import PlaylistService
from patangoma.services.renamer import RenamerService
from patangoma.services.replaygain import ReplayGainService
from patangoma.services.scanner import LibraryScanner, ScanSummary


class PataNgomaApplication:
    """The central application platform facade consumed by GUI, TUI, and CLI frontends."""

    def __init__(
        self,
        backend: AudioBackendPort | None = None,
        plugin_registry: PluginRegistry | None = None,
        config: ConfigurationManager | None = None,
        audit_journal: AuditJournal | None = None,
        job_manager: JobManager | None = None,
        event_bus: EventBus | None = None,
    ) -> None:
        self.backend = backend or MediaFileAudioBackend()
        self.plugins = plugin_registry or create_default_plugin_registry()
        self.config = config or ConfigurationManager()
        self.audit = audit_journal or AuditJournal()
        self.jobs = job_manager or JobManager()
        self.events = event_bus or EventBus()

        self.matcher = MatchingEngine()
        self.planner = PlanEngine()
        self.scanner = LibraryScanner(self.backend)
        self.reasoner = MetadataReasoner()
        self.aggregator = MetadataAggregator()
        self.artwork_service = ArtworkService()
        self.batch_service = BatchService(
            self.backend, self.planner, self.matcher, self.audit
        )
        self.duplicate_detector = DuplicateDetector()
        self.genre_normalizer = GenreNormalizer()
        self.renamer = RenamerService()
        self.replaygain_service = ReplayGainService()
        self.playlist_service = PlaylistService()

    # -------------------------------------------------------------------------
    # Core Metadata Queries & Matching
    # -------------------------------------------------------------------------

    def read_metadata(self, file_path: str | Path) -> TrackMetadata:
        """Inspect and return TrackMetadata for an audio file."""
        return self.backend.read_metadata(file_path)

    def search_metadata(
        self, query: QueryParameters, provider: str = "multi"
    ) -> list[MetadataCandidate]:
        """Search metadata candidates across configured or specified providers."""
        prov_norm = provider.lower().strip()
        if prov_norm in ("multi", "all"):
            return self.aggregator.search_all_providers(query)

        plugin = self.plugins.get_strict(prov_norm)
        return list(plugin.search_tracks(query))

    def identify_track(
        self, file_path: str | Path, provider: str = "multi"
    ) -> tuple[list[MetadataCandidate], str]:
        """Identify candidate matches for a local audio file with heuristic fallback."""
        track = self.read_metadata(file_path)
        q_title = track.title
        q_artist = track.artist
        q_album = track.album
        display_title = track.title or Path(file_path).name

        if not q_title:
            inf = self.reasoner.parse_filename(str(file_path))
            if inf.suggested_title:
                q_title = inf.suggested_title
                display_title = inf.suggested_title
                if not q_artist:
                    q_artist = inf.suggested_artist

        prov_norm = provider.lower().strip()
        if prov_norm in ("multi", "all"):
            cands = self.aggregator.search_all_providers(
                QueryParameters(
                    title=q_title,
                    artist=q_artist,
                    album=q_album,
                    isrc=track.isrc,
                )
            )
            return cands, display_title

        if prov_norm == "acoustid":
            chromaprint_tool = self.plugins.capabilities.get_media_tool("chromaprint")
            if chromaprint_tool and chromaprint_tool.is_available():
                fp_info = chromaprint_tool.fingerprint(str(file_path))
                if fp_info:
                    dur, fp = fp_info
                    acoustid_plugin = self.plugins.capabilities.get_metadata_provider(
                        "acoustid"
                    )
                    if acoustid_plugin and hasattr(
                        acoustid_plugin, "lookup_fingerprint"
                    ):
                        return (
                            acoustid_plugin.lookup_fingerprint(dur, fp),
                            display_title,
                        )

        plugin = self.plugins.get_strict(prov_norm)
        cands = list(
            plugin.search_tracks(
                QueryParameters(
                    title=q_title,
                    artist=q_artist,
                    album=q_album,
                    isrc=track.isrc,
                )
            )
        )
        return cands, display_title

    # -------------------------------------------------------------------------
    # Safe Plan / Apply & Mutation Workflow
    # -------------------------------------------------------------------------

    def create_tag_plan(
        self, file_path: str | Path, candidate: MetadataCandidate
    ) -> TagPlan:
        """Create a deterministic TagPlan comparing current file tags against chosen candidate."""
        track = self.read_metadata(file_path)
        match_res = self.matcher.evaluate_match(track, candidate)
        return self.planner.create_plan(
            track=track,
            candidate=candidate,
            confidence=match_res.confidence,
            total_score=match_res.score.total_score,
        )

    def apply_tag_plan(self, plan: TagPlan, dry_run: bool = False) -> TrackMetadata:
        """Execute and apply a validated TagPlan with pre-mutation backup."""
        track_before = self.read_metadata(plan.file_path)

        tags_to_write = {}
        for diff in plan.diffs:
            if diff.status.value != "UNCHANGED":
                tags_to_write[diff.field_name] = diff.new_value

        track_after = self.backend.write_tags(
            plan.file_path, tags_to_write, dry_run=dry_run
        )

        if not dry_run:
            self.audit.record_apply(plan, track_before, track_after)

        return track_after

    def rollback(
        self, operation_id: str | None = None, file_path: str | None = None
    ) -> TrackMetadata:
        """Rollback tags of a mutated file to its pre-mutation state."""
        if operation_id:
            return self.audit.rollback_operation(operation_id, backend=self.backend)
        if file_path:
            res = self.audit.rollback_path(file_path, backend=self.backend)
            return res[0] if res else self.read_metadata(file_path)
        return self.audit.rollback_latest(backend=self.backend)

    def get_audit_history(
        self, file_path: str | None = None, limit: int = 50
    ) -> list[AuditRecord]:
        """Query audit log history."""
        return self.audit.list_history(file_path=file_path, limit=limit)

    # -------------------------------------------------------------------------
    # Library Inspection & Batch Operations
    # -------------------------------------------------------------------------

    def scan_library(
        self, path: str | Path, recursive: bool = True
    ) -> tuple[list[TrackMetadata], ScanSummary]:
        """Scan directory and report metadata health metrics and duplicates."""
        return self.scanner.scan_directory(path, recursive=recursive)

    def batch_plan_directory(
        self,
        directory: str | Path,
        provider_name: str = "musicbrainz",
        confidence_threshold: ConfidenceLevel = ConfidenceLevel.MEDIUM,
        recursive: bool = True,
    ) -> list[TagPlan]:
        """Generate tag plans for all eligible tracks in a directory."""
        batch = self.batch_service.generate_batch_plan(
            directory,
            provider_name=provider_name,
            min_confidence=confidence_threshold,
            recursive=recursive,
        )
        return batch.matched_plans

    def batch_apply_plans(
        self, plans: Sequence[TagPlan], dry_run: bool = False
    ) -> list[TrackMetadata]:
        """Apply a collection of tag plans transactionally."""
        results = []
        for plan in plans:
            updated = self.apply_tag_plan(plan, dry_run=dry_run)
            results.append(updated)
        return results

    # -------------------------------------------------------------------------
    # Diagnostics & Platform Health
    # -------------------------------------------------------------------------

    def run_diagnostics(self) -> dict[str, Any]:
        """Run system diagnostics (network, tools, providers, permissions)."""
        return run_diagnostics()

    def list_plugins(self) -> list[Plugin]:
        """List all registered plugins."""
        return self.plugins.list_plugins()

    def get_plugin_health(self) -> dict[str, dict[str, Any]]:
        """Query health of all registered plugins."""
        return self.plugins.health_all()

    # -------------------------------------------------------------------------
    # Job Management
    # -------------------------------------------------------------------------

    def get_job(self, job_id: str) -> JobDescriptor | None:
        return self.jobs.get_job(job_id)

    def list_jobs(self, limit: int = 50) -> list[JobDescriptor]:
        return self.jobs.list_jobs(limit=limit)

    def cancel_job(self, job_id: str) -> bool:
        return self.jobs.cancel_job(job_id)
