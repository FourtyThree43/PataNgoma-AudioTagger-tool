"""Unit tests for DiscogsProvider adapter."""

from __future__ import annotations

from unittest.mock import MagicMock

from patangoma.domain.models import QueryParameters
from patangoma.providers.cache import default_provider_cache
from patangoma.providers.discogs import DiscogsProvider


def test_discogs_provider_search():
    default_provider_cache.clear()
    mock_session = MagicMock()
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "results": [
            {
                "id": 123456,
                "title": "Burna Boy - Love, Damini",
                "year": "2022",
                "genre": ["Afrobeat", "Reggae"],
                "cover_image": "https://img.discogs.com/album.jpg",
            }
        ]
    }
    mock_session.get.return_value = mock_resp

    provider = DiscogsProvider(token="mock_token", session=mock_session)
    candidates = provider.search_tracks(
        QueryParameters(title="Last Last", artist="Burna Boy")
    )

    assert len(candidates) == 1
    cand = candidates[0]
    assert cand.provider_name == "discogs"
    assert cand.provider_id == "123456"
    assert cand.title == "Last Last"
    assert cand.primary_artist == "Burna Boy"
    assert cand.year == 2022


def test_discogs_provider_release_lookup():
    mock_session = MagicMock()
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "id": 78910,
        "title": "Midnight Train",
        "artists": [{"name": "Sauti Sol"}],
        "year": 2020,
        "genres": ["Afro-Pop"],
        "images": [{"uri": "https://img.discogs.com/sautisol.jpg"}],
    }
    mock_session.get.return_value = mock_resp

    provider = DiscogsProvider(token="mock_token", session=mock_session)
    cand = provider.get_track_by_id("78910")
    assert cand is not None
    assert cand.title == "Midnight Train"
    assert cand.primary_artist == "Sauti Sol"
    assert cand.year == 2020
