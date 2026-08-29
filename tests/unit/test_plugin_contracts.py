"""Plugin contract verification test suite (Specification Section 37 & 49)."""

from __future__ import annotations

from patangoma.plugins.contracts import (
    MetadataProviderPlugin,
    Plugin,
    PluginCapability,
)
from patangoma.plugins.discovery import create_default_plugin_registry
from patangoma.plugins.metadata.acoustid import AcoustIDPlugin
from patangoma.plugins.metadata.deezer import DeezerPlugin
from patangoma.plugins.metadata.discogs import DiscogsPlugin
from patangoma.plugins.metadata.itunes import ITunesPlugin
from patangoma.plugins.metadata.lyrics import LyricsPlugin
from patangoma.plugins.metadata.musicbrainz import MusicBrainzPlugin
from patangoma.plugins.metadata.spotify import SpotifyPlugin
from patangoma.plugins.registry import PluginRegistry


def test_all_builtin_providers_satisfy_plugin_contract():
    """Verify that all 7 built-in metadata providers satisfy Plugin and MetadataProviderPlugin protocols."""
    providers = [
        MusicBrainzPlugin(),
        DeezerPlugin(),
        SpotifyPlugin(),
        DiscogsPlugin(),
        ITunesPlugin(),
        AcoustIDPlugin(),
        LyricsPlugin(),
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
    mb = MusicBrainzPlugin()

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
    """Verify create_default_plugin_registry loads all standard capability plugins."""
    reg = create_default_plugin_registry()
    plugins = reg.list_plugins()
    assert len(plugins) == 16

    expected_metadata_ids = {
        "musicbrainz",
        "deezer",
        "spotify",
        "discogs",
        "itunes",
        "acoustid",
        "lyrics",
    }
    meta_providers = {p.id for p in reg.capabilities.list_metadata_providers()}
    assert expected_metadata_ids == meta_providers
