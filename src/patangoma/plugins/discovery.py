"""Plugin discovery service for loading built-in and dynamically registered plugins."""

from __future__ import annotations

from patangoma.plugins.contracts import Plugin
from patangoma.plugins.registry import PluginRegistry


def create_default_plugin_registry() -> PluginRegistry:
    """Instantiate and populate a PluginRegistry with standard built-in providers."""
    from patangoma.providers.acoustid import AcoustIDProvider
    from patangoma.providers.deezer import DeezerProvider
    from patangoma.providers.discogs import DiscogsProvider
    from patangoma.providers.itunes import ITunesProvider
    from patangoma.providers.lyrics import LyricsProvider
    from patangoma.providers.musicbrainz import MusicBrainzProvider
    from patangoma.providers.spotify import SpotifyProvider

    registry = PluginRegistry()

    # Built-in metadata provider plugins
    builtins: list[Plugin] = [
        MusicBrainzProvider(),
        DeezerProvider(),
        SpotifyProvider(),
        DiscogsProvider(),
        ITunesProvider(),
        AcoustIDProvider(),
        LyricsProvider(),
    ]

    for p in builtins:
        registry.register(p)

    return registry
