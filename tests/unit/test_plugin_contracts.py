"""Plugin contract verification test suite (Specification Section 37 & 49)."""

from __future__ import annotations

from patangoma.plugins.contracts import (
    MetadataProviderPlugin,
    Plugin,
    PluginCapability,
)
from patangoma.plugins.discovery import create_default_plugin_registry
from patangoma.plugins.registry import PluginRegistry
from patangoma.providers.acoustid import AcoustIDProvider
from patangoma.providers.deezer import DeezerProvider
from patangoma.providers.discogs import DiscogsProvider
from patangoma.providers.itunes import ITunesProvider
from patangoma.providers.lyrics import LyricsProvider
from patangoma.providers.musicbrainz import MusicBrainzProvider
from patangoma.providers.spotify import SpotifyProvider


def test_all_builtin_providers_satisfy_plugin_contract():
    """Verify that all 7 built-in metadata providers satisfy Plugin and MetadataProviderPlugin protocols."""
    providers = [
        MusicBrainzProvider(),
        DeezerProvider(),
        SpotifyProvider(),
        DiscogsProvider(),
        ITunesProvider(),
        AcoustIDProvider(),
        LyricsProvider(),
    ]

    for prov in providers:
        assert isinstance(prov, Plugin), f"{prov.name} does not implement Plugin"
        assert isinstance(prov, MetadataProviderPlugin), (
            f"{prov.name} does not implement MetadataProviderPlugin"
        )
        assert prov.id == prov.name
        assert PluginCapability.METADATA in prov.capabilities
        health = prov.health()
        assert "status" in health
        assert health["status"] == "HEALTHY"


def test_plugin_registry_lifecycle_and_capabilities():
    """Test registry registration, enable/disable, and capability lookups."""
    registry = PluginRegistry()
    mb = MusicBrainzProvider()

    assert registry.list_plugins() == []

    # Register
    registry.register(mb)
    assert len(registry.list_plugins()) == 1
    assert registry.get("musicbrainz") is mb
    assert registry.get_strict("musicbrainz") is mb

    # Capability lookup
    metadata_plugins = registry.get_by_capability(PluginCapability.METADATA)
    assert len(metadata_plugins) == 1
    assert metadata_plugins[0].id == "musicbrainz"

    # Health check
    health_report = registry.health_all()
    assert "musicbrainz" in health_report
    assert health_report["musicbrainz"]["status"] == "HEALTHY"

    # Disable / Enable
    registry.disable("musicbrainz")
    assert registry.get("musicbrainz") is None
    assert len(registry.get_by_capability(PluginCapability.METADATA)) == 0

    registry.enable("musicbrainz")
    assert registry.get("musicbrainz") is mb

    # Unregister
    assert registry.unregister("musicbrainz") is True
    assert registry.get("musicbrainz") is None


def test_default_registry_factory():
    """Verify create_default_plugin_registry loads all standard providers."""
    reg = create_default_plugin_registry()
    plugins = reg.list_plugins()
    assert len(plugins) == 7
    expected_ids = {
        "musicbrainz",
        "deezer",
        "spotify",
        "discogs",
        "itunes",
        "acoustid",
        "lyrics",
    }
    registered_ids = {p.id for p in plugins}
    assert expected_ids == registered_ids
