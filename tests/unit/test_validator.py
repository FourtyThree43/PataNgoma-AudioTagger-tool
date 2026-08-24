"""Unit tests for FileValidator audio pre-flight integrity inspector."""

from __future__ import annotations

from pathlib import Path

from patangoma.services.validator import FileValidator


def test_validate_valid_files(
    mp3_complete: Path, flac_complete: Path, wav_complete: Path
):
    rep_mp3 = FileValidator.validate_file(mp3_complete)
    assert rep_mp3.is_readable is True
    assert rep_mp3.header_valid is True

    rep_flac = FileValidator.validate_file(flac_complete)
    assert rep_flac.is_readable is True
    assert rep_flac.header_valid is True

    rep_wav = FileValidator.validate_file(wav_complete)
    assert rep_wav.is_readable is True
    assert rep_wav.header_valid is True


def test_validate_corrupt_file(corrupt_audio_file: Path):
    rep = FileValidator.validate_file(corrupt_audio_file)
    assert rep.is_readable is False
    assert rep.header_valid is False
    assert "Invalid or corrupt" in (rep.error_message or "")


def test_validate_nonexistent_file(tmp_path: Path):
    rep = FileValidator.validate_file(tmp_path / "nonexistent.mp3")
    assert rep.is_readable is False
    assert rep.error_message == "File does not exist"
