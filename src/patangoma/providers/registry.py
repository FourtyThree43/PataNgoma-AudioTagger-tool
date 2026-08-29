"""Provider registry bridge delegating to the capability plugin subsystem."""

from __future__ import annotations

from collections.abc import Sequence

from patangoma.domain.exceptions import ProviderError
from patangoma.plugins.contracts import MetadataProviderPlugin
from patangoma.plugins.discovery import create_default_plugin_registry

_DEFAULT_REGISTRY = None


def _get_registry():
    global _DEFAULT_REGISTRY
    if _DEFAULT_REGISTRY is None:
        _DEFAULT_REGISTRY = create_default_plugin_registry()
    return _DEFAULT_REGISTRY


def get_provider(name: str) -> MetadataProviderPlugin:
    """Get metadata provider instance by name (backward compatibility bridge)."""
    norm_name = name.lower().strip()
    registry = _get_registry()
    provider = registry.capabilities.get_metadata_provider(norm_name)
    if not provider:
        available = ", ".join(
            p.name for p in registry.capabilities.list_metadata_providers()
        )
        raise ProviderError(
            f"Unknown metadata provider '{name}'. Available: {available}"
        )
    return provider


def get_available_providers() -> Sequence[str]:
    """List names of all supported metadata providers."""
    registry = _get_registry()
    return tuple(p.name for p in registry.capabilities.list_metadata_providers())
