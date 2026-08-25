"""Unit tests for Opus format support and platformdirs integration."""

from pathlib import Path

from patangoma.providers.cache import default_cache_db_path
from patangoma.services.audit import default_audit_db_path
from patangoma.services.sample_generator import create_minimal_ogg
from patangoma.services.scanner import SUPPORTED_AUDIO_EXTENSIONS
from patangoma.services.validator import FileValidator


def test_supported_audio_extensions() -> None:
    assert ".opus" in SUPPORTED_AUDIO_EXTENSIONS
    assert ".oga" in SUPPORTED_AUDIO_EXTENSIONS
    assert ".flac" in SUPPORTED_AUDIO_EXTENSIONS
    assert ".mp3" in SUPPORTED_AUDIO_EXTENSIONS


def test_opus_magic_validation(tmp_path: Path) -> None:
    ogg_file = create_minimal_ogg(tmp_path / "song.opus")
    rep = FileValidator.validate_file(ogg_file)
    assert rep.header_valid is True
    assert rep.detected_format in ("opus", "ogg")


def test_platformdirs_paths() -> None:
    audit_db = default_audit_db_path()
    assert "patangoma" in str(audit_db).lower()
    assert audit_db.name == "audit.db"

    cache_db = default_cache_db_path()
    assert "patangoma" in str(cache_db).lower()
    assert cache_db.name == "provider_cache.db"
