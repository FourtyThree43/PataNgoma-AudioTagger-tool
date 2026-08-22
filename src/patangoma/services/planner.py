"""Plan generation and validation service for safe metadata changes."""

from __future__ import annotations

from pathlib import Path
from typing import ClassVar

from patangoma.domain.models import (
    ConfidenceLevel,
    FieldDiffStatus,
    MetadataCandidate,
    TagFieldDiff,
    TagPlan,
    TrackMetadata,
)
from patangoma.services.audio_backend import compute_file_checksum


class PlanEngine:
    """Generates and parses deterministic metadata mutation plans."""

    COMPARABLE_FIELDS: ClassVar[list[tuple[str, str]]] = [
        ("title", "title"),
        ("artist", "primary_artist"),
        ("album", "album"),
        ("albumartist", "album_artist"),
        ("year", "year"),
        ("date", "release_date"),
        ("track_number", "track_number"),
        ("track_total", "track_total"),
        ("disc_number", "disc_number"),
        ("isrc", "isrc"),
        ("label", "label"),
        ("mb_trackid", "mb_trackid"),
        ("mb_artistid", "mb_artistid"),
        ("mb_albumid", "mb_albumid"),
    ]

    def create_plan(
        self,
        track: TrackMetadata,
        candidate: MetadataCandidate,
        confidence: ConfidenceLevel,
        total_score: float,
    ) -> TagPlan:
        """Create a TagPlan comparing current track metadata with candidate values."""
        checksum = compute_file_checksum(track.file_path)
        diffs: list[TagFieldDiff] = []

        for track_field, cand_field in self.COMPARABLE_FIELDS:
            old_val = getattr(track, track_field, None)
            new_val = getattr(candidate, cand_field, None)

            # Determine diff status
            if old_val == new_val or (not old_val and not new_val):
                status = FieldDiffStatus.UNCHANGED
            elif old_val is None and new_val is not None:
                status = FieldDiffStatus.ADDED
            elif old_val is not None and new_val is None:
                status = (
                    FieldDiffStatus.UNCHANGED
                )  # Don't wipe existing tags unless requested
            else:
                status = FieldDiffStatus.MODIFIED

            diffs.append(
                TagFieldDiff(
                    field_name=track_field,
                    old_value=old_val,
                    new_value=new_val if new_val is not None else old_val,
                    status=status,
                )
            )

        return TagPlan(
            file_path=track.file_path,
            provider_name=candidate.provider_name,
            provider_id=candidate.provider_id,
            confidence=confidence,
            total_score=total_score,
            diffs=diffs,
            checksum_pre=checksum,
        )

    def export_plan_to_json(self, plan: TagPlan, indent: int = 2) -> str:
        """Serialize plan to JSON string."""
        return plan.model_dump_json(indent=indent)

    def load_plan_from_json(self, json_str: str) -> TagPlan:
        """Deserialize plan from JSON string."""
        return TagPlan.model_validate_json(json_str)

    def save_plan_file(self, plan: TagPlan, output_path: str | Path) -> Path:
        """Save plan to a .json file on disk."""
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(self.export_plan_to_json(plan), encoding="utf-8")
        return out
