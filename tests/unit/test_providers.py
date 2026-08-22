"""Unit tests for MetadataProvider implementations and ProviderRegistry."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from patangoma.domain.exceptions import (
    ProviderAuthenticationError,
    ProviderError,
)
from patangoma.domain.models import QueryParameters
from patangoma.providers.base import MetadataProvider
from patangoma.providers.deezer import DeezerProvider
from patangoma.providers.musicbrainz import MusicBrainzProvider
from patangoma.providers.registry import get_available_providers, get_provider
from patangoma.providers.spotify import SpotifyProvider


def test_provider_registry():
    providers = get_available_providers()
    assert "musicbrainz" in providers
    assert "deezer" in providers
    assert "spotify" in providers

    mb_prov = get_provider("musicbrainz")
    assert isinstance(mb_prov, MetadataProvider)
    assert mb_prov.name == "musicbrainz"

    with pytest.raises(ProviderError):
        get_provider("nonexistent_provider")


@patch("musicbrainzngs.search_recordings")
def test_musicbrainz_provider_search(mock_search):
    mock_search.return_value = {
        "recording-list": [
            {
                "id": "rec-1",
                "title": "Kupe",
                "artist-credit": [{"artist": {"name": "A-Pass", "id": "art-1"}}],
                "release-list": [
                    {
                        "id": "rel-1",
                        "title": "Kupe Album",
                        "date": "2018-04-12",
                    }
                ],
                "length": 210000,
            }
        ]
    }

    provider = MusicBrainzProvider()
    query = QueryParameters(title="Kupe", artist="A-Pass")
    candidates = provider.search_tracks(query)

    assert len(candidates) == 1
    cand = candidates[0]
    assert cand.provider_name == "musicbrainz"
    assert cand.provider_id == "rec-1"
    assert cand.title == "Kupe"
    assert cand.artists == ["A-Pass"]
    assert cand.album == "Kupe Album"
    assert cand.duration_seconds == 210.0


def test_deezer_provider_search_mock():
    mock_client = MagicMock()
    mock_item = MagicMock()
    mock_item.as_dict.return_value = {
        "id": 12345,
        "title": "Jerusalema",
        "artist": {"name": "Master KG"},
        "album": {
            "title": "Jerusalema Deluxe",
            "cover_big": "https://img.deezer.com/cov.jpg",
        },
        "duration": 340,
    }
    mock_client.search.return_value = [mock_item]

    provider = DeezerProvider(client=mock_client)
    query = QueryParameters(title="Jerusalema", artist="Master KG")
    candidates = provider.search_tracks(query)

    assert len(candidates) == 1
    cand = candidates[0]
    assert cand.provider_name == "deezer"
    assert cand.provider_id == "12345"
    assert cand.title == "Jerusalema"
    assert cand.artists == ["Master KG"]
    assert cand.album == "Jerusalema Deluxe"
    assert cand.duration_seconds == 340.0


def test_spotify_provider_missing_credentials():
    provider = SpotifyProvider(client_id=None, client_secret=None)
    with patch.dict("os.environ", {}, clear=True):
        # Explicitly pass empty credentials
        provider._client_id = None
        provider._client_secret = None
        with pytest.raises(ProviderAuthenticationError):
            provider.search_tracks(QueryParameters(title="Song"))
