"""Unit tests for RenamerService and path sanitization."""

from __future__ import annotations

from pathlib import Path

from patangoma.domain.models import TrackMetadata
from patangoma.services.renamer import RenamerService, sanitize_filename_component


def test_sanitize_filename_component():
    assert sanitize_filename_component("AC/DC: Live*") == "AC-DC-Live"
    assert sanitize_filename_component('Artist <name>? "cool"') == "Artist name cool"
    assert sanitize_filename_component(None, fallback="Fallback") == "Fallback"


def test_renamer_preview_and_rename(tmp_path: Path):
    renamer = RenamerService()
    f = tmp_path / "original_file.mp3"
    f.write_text("dummy audio")

    track = TrackMetadata(
        file_path=str(f),
        file_format="mp3",
        title="Last Last",
        artist="Burna Boy",
        album="Love, Damini",
        track_number=1,
    )

    rendered = renamer.render_pattern(track)
    assert rendered == "01 - Burna Boy - Last Last.mp3"

    preview = renamer.preview_rename(track)
    assert preview.name == "01 - Burna Boy - Last Last.mp3"

    # Actual rename
    old_p, new_p = renamer.rename_track(track, dry_run=False)
    assert not old_p.exists()
    assert new_p.exists()
    assert new_p.name == "01 - Burna Boy - Last Last.mp3"
