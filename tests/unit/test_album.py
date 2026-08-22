"""Unit and characterization tests for AlbumInfo."""

from __future__ import annotations

from pathlib import Path

from patangoma.album import AlbumInfo
from patangoma.track import TrackInfo


def test_albuminfo_init_and_tracks(mp3_complete: Path, mp3_empty: Path):
    track1 = TrackInfo(str(mp3_complete))
    track2 = TrackInfo(str(mp3_empty))

    album = AlbumInfo(str(mp3_complete), [track1])
    assert len(album.tracks) == 1
    assert album.tracks[0].title == track1.title

    album.add_track(track2)
    assert len(album.tracks) == 2


def test_albuminfo_get_params(mp3_complete: Path):
    track = TrackInfo(str(mp3_complete))
    album = AlbumInfo(str(mp3_complete), [track])
    params = album.get_params()
    assert isinstance(params, dict)
    assert "title" not in params
    assert "artist" not in params
