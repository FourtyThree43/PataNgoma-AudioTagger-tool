"""Batch processing service for scanning, planning, and applying metadata changes across libraries."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field

from patangoma.domain.exceptions import AudioFileError, ProviderError
from patangoma.domain.models import (
    AuditRecord,
    ConfidenceLevel,
    FieldDiffStatus,
    QueryParameters,
    TagPlan,
)
from patangoma.matching.matcher import MatchingEngine
from patangoma.providers.registry import get_provider
from patangoma.services.audio_backend import AudioBackend
from patangoma.services.audit import AuditJournal
from patangoma.services.planner import PlanEngine
from patangoma.services.scanner import LibraryScanner


class BatchPlan(BaseModel):
    """Collection of plans for multiple audio files in a library."""

    root_directory: str
    provider_name: str
    total_files: int
    matched_plans: list[TagPlan] = Field(default_factory=list)
    unmatched_files: list[str] = Field(default_factory=list)
    skipped_files: list[str] = Field(default_factory=list)


class BatchService:
    """Service to generate and execute batch plans across music libraries."""

    def __init__(
        self,
        backend: AudioBackend | None = None,
        planner: PlanEngine | None = None,
        matcher: MatchingEngine | None = None,
        journal: AuditJournal | None = None,
    ) -> None:
        self.backend = backend or AudioBackend()
        self.planner = planner or PlanEngine()
        self.matcher = matcher or MatchingEngine()
        self.journal = journal or AuditJournal()
        self.scanner = LibraryScanner(self.backend)

    def generate_batch_plan(
        self,
        root_dir: str | Path,
        provider_name: str = "musicbrainz",
        min_confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM,
        recursive: bool = True,
    ) -> BatchPlan:
        """Scan directory and generate a BatchPlan matching each track with provider metadata."""
        path = Path(root_dir)
        files = self.scanner.discover_files(path, recursive=recursive)
        prov = get_provider(provider_name)

        batch = BatchPlan(
            root_directory=str(path.resolve()),
            provider_name=provider_name,
            total_files=len(files),
        )

        min_scores = {
            ConfidenceLevel.EXACT: 0.95,
            ConfidenceLevel.HIGH: 0.80,
            ConfidenceLevel.MEDIUM: 0.60,
            ConfidenceLevel.LOW: 0.40,
        }
        threshold = min_scores.get(min_confidence, 0.60)

        for file_path in files:
            try:
                track = self.backend.read_metadata(file_path)
            except AudioFileError:
                batch.skipped_files.append(str(file_path))
                continue

            query = QueryParameters(
                title=track.title or file_path.stem,
                artist=track.artist,
                album=track.album,
            )

            try:
                candidates = prov.search_tracks(query)
            except ProviderError:
                batch.unmatched_files.append(str(file_path))
                continue

            if not candidates:
                batch.unmatched_files.append(str(file_path))
                continue

            ranked = self.matcher.rank_candidates(track, candidates)
            best = ranked[0]

            if best.score.total_score >= threshold:
                plan = self.planner.create_plan(
                    track=track,
                    candidate=best.candidate,
                    confidence=best.confidence,
                    total_score=best.score.total_score,
                )
                if plan.has_changes:
                    batch.matched_plans.append(plan)
                else:
                    batch.skipped_files.append(str(file_path))
            else:
                batch.unmatched_files.append(str(file_path))

        return batch

    def apply_batch_plan(
        self,
        batch_plan: BatchPlan,
        dry_run: bool = False,
    ) -> list[AuditRecord]:
        """Apply all plans in a BatchPlan with audit log snapshots."""
        records: list[AuditRecord] = []

        for plan in batch_plan.matched_plans:
            updates = {}
            for diff in plan.diffs:
                if diff.status in (FieldDiffStatus.ADDED, FieldDiffStatus.MODIFIED):
                    updates[diff.field_name] = diff.new_value

            if not updates:
                continue

            track_before = self.backend.read_metadata(plan.file_path)

            if dry_run:
                updated = self.backend.write_tags(plan.file_path, updates, dry_run=True)
            else:
                updated = self.backend.write_tags(
                    plan.file_path, updates, dry_run=False
                )
                rec = self.journal.record_apply(plan, track_before, updated)
                records.append(rec)

        return records

    def export_batch_plan(self, batch_plan: BatchPlan, output_path: str | Path) -> Path:
        """Save a batch plan to disk as formatted JSON."""
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(batch_plan.model_dump_json(indent=2), encoding="utf-8")
        return out

    def load_batch_plan(self, input_path: str | Path) -> BatchPlan:
        """Load a batch plan from a JSON file."""
        return BatchPlan.model_validate_json(
            Path(input_path).read_text(encoding="utf-8")
        )
