"""Characterization tests for legacy provider adapters (MusicBrainz, Deezer)."""

from __future__ import annotations

import datetime

from patangoma.dz import DeezerAPI
from patangoma.mb import MusicBrainzAPI


def test_musicbrainz_translation():
    api = MusicBrainzAPI()
    flattened_sample = {
        "title": "Midnight City",
        "artist-credit[0].name": "M83",
        "artist-credit[0].artist.id": "mb-artist-123",
        "release-list[0].title": "Hurry Up, We're Dreaming",
        "release-list[0].id": "mb-release-456",
        "release-list[0].date": "2011-10-18",
        "release-list[0].medium-list[0].position": 1,
        "release-list[0].medium-list[0].track-count": 11,
    }

    translated = api.translate_mb_result(flattened_sample)
    assert translated["title"] == "Midnight City"
    assert translated["artist"] == "M83"
    assert translated["mb_artistid"] == "mb-artist-123"
    assert translated["album"] == "Hurry Up, We're Dreaming"
    assert translated["mb_albumid"] == "mb-release-456"
    assert translated["date"] == datetime.date(2011, 10, 18)
    assert translated["track"] == 1
    assert translated["tracktotal"] == 11


def test_musicbrainz_year_only_translation():
    api = MusicBrainzAPI()
    flattened_sample = {
        "title": "Old Song",
        "release-list[0].date": "1985",
    }
    translated = api.translate_mb_result(flattened_sample)
    assert translated["date"] == datetime.date(1985, 1, 1)


def test_deezer_api_init():
    api = DeezerAPI()
    assert api.client is not None
