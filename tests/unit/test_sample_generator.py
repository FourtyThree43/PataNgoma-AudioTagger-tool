"""Unit tests for sample library generator."""

from __future__ import annotations

from pathlib import Path

from patangoma.services.sample_generator import generate_sample_library


def test_generate_sample_library(tmp_path: Path):
    target = tmp_path / "sample_music"
    created = generate_sample_library(target)

    assert len(created["complete"]) == 3
    assert len(created["missing_metadata"]) == 2
    assert len(created["unicode"]) == 1
    assert len(created["corrupt"]) == 1

    # Check files exist on disk
    for _cat, file_paths in created.items():
        for p in file_paths:
            assert Path(p).exists()
