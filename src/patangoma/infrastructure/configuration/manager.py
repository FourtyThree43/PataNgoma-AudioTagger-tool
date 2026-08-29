"""Configuration and secrets manager for PataNgoma platform."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import platformdirs
import yaml

from patangoma.domain.exceptions import ConfigurationError


def default_config_path() -> Path:
    """Get the standard OS configuration file path for PataNgoma."""
    if env_conf := os.getenv("PATANGOMA_CONFIG"):
        return Path(env_conf)
    try:
        conf_dir = Path(platformdirs.user_config_dir("patangoma", appauthor=False))
        return conf_dir / "config.yaml"
    except OSError:
        return Path.home() / ".config" / "patangoma" / "config.yaml"


@dataclass
class ConfigurationManager:
    """Central configuration service with hierarchical overrides."""

    config_path: Path = field(default_factory=default_config_path)
    _values: dict[str, Any] = field(default_factory=dict)
    _secrets: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self._load_defaults()
        self._load_from_file()
        self._load_from_env()

    def _load_defaults(self) -> None:
        self._values = {
            "default_provider": "multi",
            "confidence_threshold": "HIGH",
            "dry_run": False,
            "backup_enabled": True,
            "artwork_max_dimension": 1200,
            "cache_ttl_seconds": 86400,
            "max_concurrency": 4,
            "log_level": "INFO",
        }

    def _load_from_file(self) -> None:
        if self.config_path.is_file():
            try:
                with self.config_path.open("r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                    if isinstance(data, dict):
                        self._values.update(data.get("settings", {}))
                        self._secrets.update(data.get("secrets", {}))
            except Exception as e:
                raise ConfigurationError(
                    f"Failed to read config file {self.config_path}", str(e)
                ) from e

    def _load_from_env(self) -> None:
        # Check standard PATANGOMA_* environment variables
        for key, val in os.environ.items():
            if key.startswith("PATANGOMA_"):
                opt = key[10:].lower()
                self._values[opt] = val
        # Check provider API keys and tokens
        for secret_key in (
            "SPOTIPY_CLIENT_ID",
            "SPOTIPY_CLIENT_SECRET",
            "DISCOGS_USER_TOKEN",
            "ACOUSTID_API_KEY",
            "GENIUS_ACCESS_TOKEN",
        ):
            if val := os.getenv(secret_key):
                self._secrets[secret_key] = val

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        return self._values.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set in-memory configuration value."""
        self._values[key] = value

    def get_secret(self, key: str) -> str | None:
        """Get secret / API token."""
        return self._secrets.get(key) or os.getenv(key)

    def set_secret(self, key: str, secret_value: str) -> None:
        """Set in-memory secret."""
        self._secrets[key] = secret_value

    def save(self, target_path: Path | None = None) -> None:
        """Persist current configuration to file."""
        dest = target_path or self.config_path
        dest.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "settings": self._values,
            "secrets": {k: "***" for k in self._secrets},
        }
        with dest.open("w", encoding="utf-8") as f:
            yaml.dump(payload, f, default_flow_style=False)
