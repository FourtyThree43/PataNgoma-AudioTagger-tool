"""Multi-provider metadata aggregation and conflict resolution engine."""

from __future__ import annotations

import logging
from collections.abc import Sequence
from concurrent.futures import ThreadPoolExecutor, as_completed

from patangoma.domain.models import (
    ConfidenceLevel,
    MatchResult,
    MetadataCandidate,
    QueryParameters,
    TrackMetadata,
)
from patangoma.matching.matcher import MatchingEngine
from patangoma.plugins.contracts import MetadataProviderPlugin
from patangoma.providers.registry import get_available_providers, get_provider

logger = logging.getLogger(__name__)


class MetadataAggregator:
    """Queries multiple metadata providers concurrently and aggregates candidates with conflict resolution."""

    def __init__(
        self,
        providers: Sequence[MetadataProviderPlugin | str] | None = None,
        matcher: MatchingEngine | None = None,
    ) -> None:
        self.matcher = matcher or MatchingEngine()
        self.providers: list[MetadataProviderPlugin] = []
        if providers:
            for p in providers:
                if isinstance(p, str):
                    self.providers.append(get_provider(p))
                else:
                    self.providers.append(p)
        else:
            # Default to all registered providers
            for name in get_available_providers():
                try:
                    self.providers.append(get_provider(name))
                except Exception as e:
                    logger.debug(
                        "Provider %s unavailable during aggregator init: %s",
                        name,
                        e,
                    )

    def search_all_providers(
        self, query: QueryParameters, max_workers: int = 5
    ) -> list[MetadataCandidate]:
        """Query all configured providers concurrently and return aggregated list of candidates."""
        all_candidates: list[MetadataCandidate] = []

        def _search(prov: MetadataProviderPlugin) -> list[MetadataCandidate]:
            try:
                return list(prov.search_tracks(query))
            except Exception as e:
                logger.debug(
                    "Aggregator search failed for provider %s: %s", prov.name, e
                )
                return []

        if len(self.providers) > 1 and max_workers > 1:
            with ThreadPoolExecutor(
                max_workers=min(max_workers, len(self.providers))
            ) as executor:
                futures = [executor.submit(_search, p) for p in self.providers]
                for fut in as_completed(futures):
                    all_candidates.extend(fut.result())
        else:
            for p in self.providers:
                all_candidates.extend(_search(p))

        return all_candidates

    def find_best_match(
        self,
        track: TrackMetadata,
        query: QueryParameters | None = None,
        min_confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM,
    ) -> tuple[MatchResult | None, list[MatchResult]]:
        """Search all providers and rank results against track metadata."""
        search_query = query or QueryParameters(
            title=track.title,
            artist=track.artist,
            album=track.album,
            isrc=track.isrc,
            year=track.year,
        )

        candidates = self.search_all_providers(search_query)
        if not candidates:
            return None, []

        ranked_results = self.matcher.rank_candidates(track, candidates)
        best = ranked_results[0] if ranked_results else None
        return (best if best and best.is_acceptable else None), ranked_results

    def merge_candidates(
        self,
        primary_candidate: MetadataCandidate,
        secondary_candidates: Sequence[MetadataCandidate],
    ) -> MetadataCandidate:
        """Resolve conflicts and merge missing fields from secondary candidates into primary."""
        merged_dict = primary_candidate.model_dump()

        # Aggregate unique genres
        genres_set = set(primary_candidate.genres)
        for cand in secondary_candidates:
            for g in cand.genres:
                if g and g not in genres_set:
                    genres_set.add(g)

        merged_dict["genres"] = sorted(genres_set)

        # Fill in missing fields from highest-confidence secondary candidates
        for cand in secondary_candidates:
            if not merged_dict.get("album") and cand.album:
                merged_dict["album"] = cand.album
            if not merged_dict.get("album_artist") and cand.album_artist:
                merged_dict["album_artist"] = cand.album_artist
            if not merged_dict.get("year") and cand.year:
                merged_dict["year"] = cand.year
            if not merged_dict.get("release_date") and cand.release_date:
                merged_dict["release_date"] = cand.release_date
            if not merged_dict.get("isrc") and cand.isrc:
                merged_dict["isrc"] = cand.isrc
            if not merged_dict.get("track_number") and cand.track_number:
                merged_dict["track_number"] = cand.track_number
            if not merged_dict.get("artwork_url") and cand.artwork_url:
                merged_dict["artwork_url"] = cand.artwork_url
            if not merged_dict.get("mb_trackid") and cand.mb_trackid:
                merged_dict["mb_trackid"] = cand.mb_trackid
            if not merged_dict.get("mb_artistid") and cand.mb_artistid:
                merged_dict["mb_artistid"] = cand.mb_artistid
            if not merged_dict.get("mb_albumid") and cand.mb_albumid:
                merged_dict["mb_albumid"] = cand.mb_albumid

        return MetadataCandidate.model_validate(merged_dict)
