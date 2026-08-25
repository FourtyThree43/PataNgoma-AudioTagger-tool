"""Unit tests for PlaylistService (M3U8 export and Cue sheet parser)."""

from pathlib import Path

from patangoma.services.playlist import PlaylistService
from patangoma.services.sample_generator import create_minimal_mp3


def test_export_m3u8_playlist(tmp_path: Path) -> None:
    f1 = create_minimal_mp3(
        tmp_path / "01.mp3", {"title": "Song One", "artist": "Artist A"}
    )
    f2 = create_minimal_mp3(
        tmp_path / "02.mp3", {"title": "Song Two", "artist": "Artist B"}
    )

    ps = PlaylistService()
    out = tmp_path / "playlist.m3u8"
    ps.export_m3u8([f1, f2], out, relative_paths=True)

    assert out.exists()
    content = out.read_text(encoding="utf-8")
    assert "#EXTM3U" in content
    assert "01.mp3" in content
    assert "02.mp3" in content


def test_parse_cue_sheet(tmp_path: Path) -> None:
    cue_content = """
    PERFORMER "Album Artist"
    TITLE "Greatest Hits"
    FILE "cd.flac" WAVE
      TRACK 01 AUDIO
        TITLE "First Track"
        PERFORMER "Track Performer"
        INDEX 01 00:00:00
      TRACK 02 AUDIO
        TITLE "Second Track"
        INDEX 01 03:45:00
    """
    cue_file = tmp_path / "album.cue"
    cue_file.write_text(cue_content, encoding="utf-8")

    ps = PlaylistService()
    tracks = ps.parse_cue_sheet(cue_file)

    assert len(tracks) == 2
    assert tracks[0].track_number == 1
    assert tracks[0].title == "First Track"
    assert tracks[0].artist == "Track Performer"
    assert tracks[0].index_time == "00:00:00"

    assert tracks[1].track_number == 2
    assert tracks[1].title == "Second Track"
    assert tracks[1].artist == "Album Artist"
