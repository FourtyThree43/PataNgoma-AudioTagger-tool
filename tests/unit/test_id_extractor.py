"""Unit tests for ID extraction regexes from external services."""

from __future__ import annotations

import re

from patangoma.id_extractor import (
    beatport_id_regex,
    deezer_id_regex,
    extract_discogs_id_regex,
    spotify_id_regex,
)


def test_spotify_id_regex():
    pattern = spotify_id_regex["pattern"].format("track")
    url = "https://open.spotify.com/track/3n3Ppam7vgaVa1iaRUc9Lp"
    match = re.search(pattern, url)
    assert match is not None
    assert match.group(spotify_id_regex["match_group"]) == "3n3Ppam7vgaVa1iaRUc9Lp"

    raw_id = "3n3Ppam7vgaVa1iaRUc9Lp"
    match_raw = re.search(pattern, raw_id)
    assert match_raw is not None
    assert match_raw.group(spotify_id_regex["match_group"]) == "3n3Ppam7vgaVa1iaRUc9Lp"


def test_deezer_id_regex():
    pattern = deezer_id_regex["pattern"].format("track")
    url = "https://www.deezer.com/en/track/3135556"
    match = re.search(pattern, url)
    assert match is not None
    assert match.group(deezer_id_regex["match_group"]) == "3135556"


def test_beatport_id_regex():
    url = "https://www.beatport.com/release/summer-vibes/123456"
    match = re.search(beatport_id_regex["pattern"], url)
    assert match is not None
    assert match.group(beatport_id_regex["match_group"]) == "123456"


def test_discogs_id_extractor():
    assert extract_discogs_id_regex("123456") == 123456
    assert extract_discogs_id_regex("[r123456]") == 123456
    assert (
        extract_discogs_id_regex("https://www.discogs.com/release/123456-Artist-Album")
        == 123456
    )
    assert extract_discogs_id_regex("invalid-id-string") is None
