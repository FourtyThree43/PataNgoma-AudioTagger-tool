"""Unit and characterization tests for TrackInfo and BaseModel."""

from __future__ import annotations

from pathlib import Path

from patangoma.track import TrackInfo


def test_trackinfo_load_complete_mp3(mp3_complete: Path, complete_tags: dict):
    track = TrackInfo(str(mp3_complete))
    assert track.title == complete_tags["title"]
    assert track.artist == complete_tags["artist"]
    assert track.album == complete_tags["album"]
    assert track.genre == complete_tags["genre"]
    assert track.year == complete_tags["year"]
    assert track.track == complete_tags["track"]


def test_trackinfo_load_flac(flac_complete: Path, complete_tags: dict):
    track = TrackInfo(str(flac_complete))
    assert track.title == complete_tags["title"]
    assert track.artist == complete_tags["artist"]
    assert track.album == complete_tags["album"]


def test_trackinfo_missing_title(mp3_missing_title: Path):
    track = TrackInfo(str(mp3_missing_title))
    assert track.title is None
    assert track.artist == "Unknown Artist"


def test_trackinfo_missing_artist(mp3_missing_artist: Path):
    track = TrackInfo(str(mp3_missing_artist))
    assert track.title == "Mystery Track"
    assert track.artist is None


def test_trackinfo_as_dict(mp3_complete: Path, complete_tags: dict):
    track = TrackInfo(str(mp3_complete))
    meta_dict = track.as_dict()
    assert isinstance(meta_dict, dict)
    assert meta_dict.get("title") == complete_tags["title"]
    assert meta_dict.get("artist") == complete_tags["artist"]


def test_trackinfo_get_params(mp3_complete: Path):
    track = TrackInfo(str(mp3_complete))
    params = track.get_params()
    # get_params excludes art, title, artist, lyrics, images
    assert "title" not in params
    assert "artist" not in params
    assert "art" not in params
    assert "lyrics" not in params
    assert "album" in params


def test_trackinfo_batch_update_and_save(mp3_empty: Path):
    track = TrackInfo(str(mp3_empty))
    assert track.title is None

    track.batch_update_metadata(
        {"title": "Updated Title", "artist": "Updated Artist", "year": 2025}
    )
    track.save()

    # Re-open file to confirm disk mutation
    reloaded = TrackInfo(str(mp3_empty))
    assert reloaded.title == "Updated Title"
    assert reloaded.artist == "Updated Artist"
    assert reloaded.year == 2025


def test_trackinfo_has_changed(mp3_complete: Path):
    track = TrackInfo(str(mp3_complete))
    old_meta = track.as_dict()

    new_meta_same = dict(old_meta)
    assert track.has_changed(new_meta_same, old_meta) is False

    new_meta_diff = dict(old_meta)
    new_meta_diff["title"] = "Different Title"
    assert track.has_changed(new_meta_diff, old_meta) is True


def test_trackinfo_delete_metadata(mp3_complete: Path):
    track = TrackInfo(str(mp3_complete))
    assert track.title is not None

    track.delete()

    reloaded = TrackInfo(str(mp3_complete))
    assert reloaded.title is None
