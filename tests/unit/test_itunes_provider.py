"""Unit tests for iTunesProvider adapter."""

from __future__ import annotations

from unittest.mock import MagicMock

from patangoma.domain.models import QueryParameters
from patangoma.providers.cache import default_provider_cache
from patangoma.providers.itunes import ITunesProvider


def test_itunes_provider_search():
    default_provider_cache.clear()
    mock_session = MagicMock()
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "resultCount": 1,
        "results": [
            {
                "trackId": 1440857781,
                "trackName": "Starboy",
                "artistName": "The Weeknd",
                "collectionName": "Starboy",
                "releaseDate": "2016-11-25T08:00:00Z",
                "primaryGenreName": "R&B/Soul",
                "trackNumber": 1,
                "trackCount": 18,
                "discNumber": 1,
                "trackTimeMillis": 230453,
                "artworkUrl100": "https://is1-ssl.mzstatic.com/image/thumb/Music/100x100bb.jpg",
            }
        ],
    }
    mock_session.get.return_value = mock_resp

    provider = ITunesProvider(session=mock_session)
    candidates = provider.search_tracks(
        QueryParameters(title="Starboy", artist="The Weeknd")
    )

    assert len(candidates) == 1
    cand = candidates[0]
    assert cand.provider_name == "itunes"
    assert cand.provider_id == "1440857781"
    assert cand.title == "Starboy"
    assert cand.primary_artist == "The Weeknd"
    assert cand.album == "Starboy"
    assert cand.year == 2016
    assert cand.track_number == 1
    assert "600x600" in (cand.artwork_url or "")


def test_itunes_provider_lookup():
    mock_session = MagicMock()
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "resultCount": 1,
        "results": [
            {
                "trackId": 99999,
                "trackName": "Blinding Lights",
                "artistName": "The Weeknd",
                "collectionName": "After Hours",
                "releaseDate": "2020-03-20T00:00:00Z",
                "primaryGenreName": "Pop",
                "trackNumber": 9,
            }
        ],
    }
    mock_session.get.return_value = mock_resp

    provider = ITunesProvider(session=mock_session)
    cand = provider.get_track_by_id("99999")
    assert cand is not None
    assert cand.title == "Blinding Lights"
    assert cand.year == 2020
