"""Unit and characterization tests for DataStore."""

from __future__ import annotations

from pathlib import Path

from patangoma.data_store import DataStore


def test_datastore_yaml_roundtrip(tmp_path: Path):
    store_file = tmp_path / "store.yaml"
    ds = DataStore(file_path=str(store_file), fmt="yaml")

    ds.add_metadata("musicbrainz", {"id": "123", "title": "Song A"})
    ds.add_metadata("musicbrainz", {"id": "456", "title": "Song B"})
    ds.add_metadata("deezer", {"id": "789", "title": "Song C"})

    # Reload from disk
    ds2 = DataStore(file_path=str(store_file), fmt="yaml")
    mb_data = ds2.get_metadata("musicbrainz")
    assert len(mb_data) == 2
    assert mb_data[0]["title"] == "Song A"

    dz_data = ds2.get_metadata("deezer")
    assert len(dz_data) == 1
    assert dz_data[0]["title"] == "Song C"

    all_data = ds2.get_all_metadata()
    assert "musicbrainz" in all_data
    assert "deezer" in all_data


def test_datastore_json_roundtrip(tmp_path: Path):
    store_file = tmp_path / "store.json"
    ds = DataStore(file_path=str(store_file), fmt="json")

    ds.add_metadata("spotify", {"track": "Song X", "popularity": 90})

    ds2 = DataStore(file_path=str(store_file), fmt="json")
    sp_data = ds2.get_metadata("spotify")
    assert len(sp_data) == 1
    assert sp_data[0]["track"] == "Song X"
