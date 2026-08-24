"""Album-level tracklist alignment and multi-track folder matching engine."""

from __future__ import annotations

import logging
from collections.abc import Sequence

from pydantic import BaseModel, Field

from patangoma.domain.models import (
    ConfidenceLevel,
    MatchResult,
    MetadataCandidate,
    TrackMetadata,
)
from patangoma.matching.matcher import (
    MatchingEngine,
)

logger = logging.getLogger(__name__)


class AlbumAlignment(BaseModel):
    """Alignment between local tracks and a candidate album release."""

    album_title: str
    album_artist: str
    provider_name: str
    provider_id: str
    average_score: float
    confidence: ConfidenceLevel
    aligned_tracks: list[tuple[str, str, float]] = Field(
        default_factory=list
    )  # (file_path, candidate_title, score)


class AlbumMatcher:
    """Aligns an entire folder of tracks against release tracklists."""

    def __init__(self, matcher: MatchingEngine | None = None) -> None:
        self.matcher = matcher or MatchingEngine()

    def align_tracks(
        self,
        local_tracks: Sequence[TrackMetadata],
        candidate_tracklist: Sequence[MetadataCandidate],
    ) -> tuple[list[tuple[TrackMetadata, MetadataCandidate, MatchResult]], float]:
        """Align local tracks with candidate release tracklist, returning (pairs, average_score)."""
        if not local_tracks or not candidate_tracklist:
            return [], 0.0

        matches: list[tuple[TrackMetadata, MetadataCandidate, MatchResult]] = []
        unassigned_candidates = list(candidate_tracklist)

        # 1. First pass: Match by track_number if both have track numbers
        for track in local_tracks:
            best_cand: MetadataCandidate | None = None
            best_res: MatchResult | None = None

            if track.track_number is not None:
                for cand in unassigned_candidates:
                    if cand.track_number == track.track_number:
                        res = self.matcher.evaluate_match(track, cand)
                        if res.score.total_score >= 0.5:
                            best_cand = cand
                            best_res = res
                            break

            # 2. Second pass: Match by title similarity & duration
            if best_cand is None and unassigned_candidates:
                ranked = self.matcher.rank_candidates(track, unassigned_candidates)
                if ranked and ranked[0].is_acceptable:
                    best_cand = ranked[0].candidate
                    best_res = ranked[0]

            if best_cand and best_res:
                matches.append((track, best_cand, best_res))
                unassigned_candidates.remove(best_cand)

        if not matches:
            return [], 0.0

        avg_score = sum(res.score.total_score for _, _, res in matches) / len(
            local_tracks
        )
        return matches, avg_score
