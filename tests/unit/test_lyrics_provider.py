"""Unit tests for LyricsProvider."""

from __future__ import annotations

from unittest.mock import MagicMock

from patangoma.domain.models import QueryParameters
from patangoma.providers.cache import default_provider_cache
from patangoma.providers.lyrics import LyricsProvider


def test_lyrics_provider_search():
    default_provider_cache.clear()
    mock_session = MagicMock()
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "id": 12345,
        "trackName": "Suzanna",
        "artistName": "Sauti Sol",
        "albumName": "Midnight Train",
        "duration": 230,
        "plainLyrics": "Oh Suzanna, I hope you're happy...",
        "syncedLyrics": "[00:12.50] Oh Suzanna\n[00:15.00] I hope you're happy",
    }
    mock_session.get.return_value = mock_resp

    provider = LyricsProvider(session=mock_session)
    cands = provider.search_tracks(QueryParameters(title="Suzanna", artist="Sauti Sol"))

    assert len(cands) == 1
    cand = cands[0]
    assert cand.provider_name == "lyrics"
    assert cand.title == "Suzanna"
    assert cand.primary_artist == "Sauti Sol"

    plain, synced = provider.fetch_lyrics(title="Suzanna", artist="Sauti Sol")
    assert plain == "Oh Suzanna, I hope you're happy..."
    assert "[00:12.50]" in (synced or "")
