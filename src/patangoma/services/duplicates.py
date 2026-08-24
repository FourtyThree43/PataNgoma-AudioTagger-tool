"""Duplicate audio file detection service."""

from __future__ import annotations

from collections.abc import Sequence

from pydantic import BaseModel, Field

from patangoma.domain.models import TrackMetadata
from patangoma.matching.matcher import compute_string_similarity


class DuplicateGroup(BaseModel):
    """A cluster of identified duplicate audio tracks."""

    primary_track: TrackMetadata
    duplicate_tracks: list[TrackMetadata] = Field(default_factory=list)
    reason: str


class DuplicateDetector:
    """Detects duplicate audio files across formats, directories, and bitrates."""

    @staticmethod
    def find_duplicates(tracks: Sequence[TrackMetadata]) -> list[DuplicateGroup]:
        """Group tracks into duplicate clusters by ISRC, MBID, or Title + Artist + Duration similarity."""
        groups: list[DuplicateGroup] = []
        assigned_paths: set[str] = set()

        # Sort tracks by bitrate / lossless quality descending so the highest quality becomes primary
        sorted_tracks = sorted(
            tracks,
            key=lambda t: (
                1 if (t.file_format or "").lower() in ("flac", "wav") else 0,
                t.bitrate or 0,
            ),
            reverse=True,
        )

        for i, primary in enumerate(sorted_tracks):
            if primary.file_path in assigned_paths:
                continue

            current_dups: list[TrackMetadata] = []
            reason = ""

            for secondary in sorted_tracks[i + 1 :]:
                if secondary.file_path in assigned_paths:
                    continue

                # 1. Exact ISRC or MBID match
                if primary.isrc and secondary.isrc and primary.isrc == secondary.isrc:
                    current_dups.append(secondary)
                    reason = f"ISRC match ({primary.isrc})"
                    assigned_paths.add(secondary.file_path)
                    continue

                if (
                    primary.mb_trackid
                    and secondary.mb_trackid
                    and primary.mb_trackid == secondary.mb_trackid
                ):
                    current_dups.append(secondary)
                    reason = f"MusicBrainz Track ID match ({primary.mb_trackid})"
                    assigned_paths.add(secondary.file_path)
                    continue

                # 2. Heuristic match: Title & Artist similarity + Duration within 2.0s
                if (
                    primary.title
                    and secondary.title
                    and primary.artist
                    and secondary.artist
                ):
                    t_sim = compute_string_similarity(primary.title, secondary.title)
                    a_sim = compute_string_similarity(primary.artist, secondary.artist)
                    dur_match = True
                    if primary.duration_seconds and secondary.duration_seconds:
                        dur_match = (
                            abs(primary.duration_seconds - secondary.duration_seconds)
                            <= 2.5
                        )

                    if t_sim >= 0.85 and a_sim >= 0.85 and dur_match:
                        current_dups.append(secondary)
                        reason = (
                            f"Title & Artist match ({int(t_sim * 100)}% similarity)"
                        )
                        assigned_paths.add(secondary.file_path)

            if current_dups:
                assigned_paths.add(primary.file_path)
                groups.append(
                    DuplicateGroup(
                        primary_track=primary,
                        duplicate_tracks=current_dups,
                        reason=reason,
                    )
                )

        return groups
