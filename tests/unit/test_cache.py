"""Unit tests for ProviderCache service and decorators."""

from __future__ import annotations

import time
from pathlib import Path

from patangoma.domain.models import MetadataCandidate, QueryParameters
from patangoma.services.cache import ProviderCache, cached_get_track, cached_search


def test_provider_cache_memory_and_sqlite(tmp_path: Path):
    db_file = tmp_path / "test_cache.db"
    cache = ProviderCache(db_path=db_file, default_ttl=3600)

    candidate = MetadataCandidate(
        provider_name="spotify",
        provider_id="spot-123",
        title="Test Song",
        artists=["Test Artist"],
        album="Test Album",
        year=2023,
    )

    query_params = {"title": "Test Song", "artist": "Test Artist"}

    # Initially miss
    assert cache.get_cached_candidates("spotify", "search_tracks", query_params) is None

    # Set and retrieve from memory
    cache.set_cached_candidates("spotify", "search_tracks", query_params, [candidate])
    hits = cache.get_cached_candidates("spotify", "search_tracks", query_params)
    assert hits is not None
    assert len(hits) == 1
    assert hits[0].title == "Test Song"
    assert hits[0].provider_id == "spot-123"

    # New cache instance on same db file tests SQLite persistence
    cache2 = ProviderCache(db_path=db_file, default_ttl=3600)
    hits2 = cache2.get_cached_candidates("spotify", "search_tracks", query_params)
    assert hits2 is not None
    assert len(hits2) == 1
    assert hits2[0].title == "Test Song"


def test_provider_cache_single_candidate(tmp_path: Path):
    db_file = tmp_path / "test_cache_single.db"
    cache = ProviderCache(db_path=db_file, default_ttl=3600)

    candidate = MetadataCandidate(
        provider_name="deezer",
        provider_id="dz-456",
        title="Deezer Track",
        artists=["Deezer Artist"],
    )

    cache.set_cached_candidate("deezer", "get_track_by_id", "dz-456", candidate)
    hit = cache.get_cached_candidate("deezer", "get_track_by_id", "dz-456")
    assert hit is not None
    assert hit.title == "Deezer Track"
    assert hit.provider_id == "dz-456"

    # Test clear
    cache.clear()
    assert cache.get_cached_candidate("deezer", "get_track_by_id", "dz-456") is None


def test_provider_cache_ttl_expiration(tmp_path: Path):
    db_file = tmp_path / "test_cache_ttl.db"
    cache = ProviderCache(db_path=db_file, default_ttl=1)

    candidate = MetadataCandidate(
        provider_name="musicbrainz",
        provider_id="mb-789",
        title="Expiring Track",
        artists=["Expiring Artist"],
    )

    cache.set_cached_candidate(
        "musicbrainz", "get_track_by_id", "mb-789", candidate, ttl=1
    )
    assert (
        cache.get_cached_candidate("musicbrainz", "get_track_by_id", "mb-789")
        is not None
    )

    time.sleep(1.1)
    # Memory cache expired and SQLite row expired
    assert (
        cache.get_cached_candidate("musicbrainz", "get_track_by_id", "mb-789") is None
    )


def test_cache_decorators(tmp_path: Path):
    db_file = tmp_path / "test_cache_dec.db"
    cache = ProviderCache(db_path=db_file, default_ttl=3600)

    call_count = {"search": 0, "get": 0}

    class MockProvider:
        name = "mock_provider"

        @cached_search(cache=cache)
        def search_tracks(self, query: QueryParameters) -> list[MetadataCandidate]:
            call_count["search"] += 1
            return [
                MetadataCandidate(
                    provider_name="mock_provider",
                    provider_id="mock-1",
                    title=query.title or "Untitled",
                    artists=[query.artist or "Unknown"],
                )
            ]

        @cached_get_track(cache=cache)
        def get_track_by_id(self, track_id: str) -> MetadataCandidate | None:
            call_count["get"] += 1
            return MetadataCandidate(
                provider_name="mock_provider",
                provider_id=track_id,
                title="Mock ID Title",
                artists=["Mock Artist"],
            )

    provider = MockProvider()
    query = QueryParameters(title="Hello", artist="Adele")

    # 1. First search -> call_count = 1
    res1 = provider.search_tracks(query)
    assert len(res1) == 1
    assert call_count["search"] == 1

    # 2. Second search with same query -> returns cached result, call_count remains 1
    res2 = provider.search_tracks(query)
    assert len(res2) == 1
    assert res2[0].title == "Hello"
    assert call_count["search"] == 1

    # 3. get_track_by_id cached
    t1 = provider.get_track_by_id("mock-100")
    assert t1 is not None
    assert call_count["get"] == 1

    t2 = provider.get_track_by_id("mock-100")
    assert t2 is not None
    assert call_count["get"] == 1
