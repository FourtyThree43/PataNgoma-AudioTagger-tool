"""Unit tests for SQLite FileStorage in database.py."""

from __future__ import annotations

from pathlib import Path

from patangoma.database import FileStorage


def test_filestorage_sqlite_crud(tmp_path: Path):
    db_file = tmp_path / "test_library.db"
    initial_meta = {
        "title": "Initial Title",
        "artist": "Initial Artist",
        "album": "Initial Album",
        "year": 2020,
    }

    storage = FileStorage(str(db_file), track_metadata=initial_meta)
    storage.add_track_metadata(initial_meta)

    record = storage.get_track_metadata(1)
    assert record is not None
    # record[0] is id, followed by columns
    assert "Initial Title" in record
    assert "Initial Artist" in record

    storage.close()
