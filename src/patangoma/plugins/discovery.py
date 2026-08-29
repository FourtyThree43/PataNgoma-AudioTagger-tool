"""Plugin discovery service for loading built-in and dynamically registered plugins."""

from __future__ import annotations

from patangoma.plugins.contracts import Plugin
from patangoma.plugins.registry import PluginRegistry


def create_default_plugin_registry() -> PluginRegistry:
    """Instantiate and populate a PluginRegistry with all standard built-in capability plugins."""
    from patangoma.plugins.artwork.coverartarchive import CoverArtArchivePlugin
    from patangoma.plugins.download.aria2 import Aria2DownloadPlugin
    from patangoma.plugins.download.yt_dlp import YtDlpDownloadPlugin
    from patangoma.plugins.export.exporters import (
        CSVExporterPlugin,
        JSONExporterPlugin,
        M3UPlaylistExporterPlugin,
    )
    from patangoma.plugins.import_.importers import JSONImporterPlugin
    from patangoma.plugins.media.chromaprint import ChromaprintMediaPlugin
    from patangoma.plugins.media.ffmpeg import FFmpegMediaPlugin
    from patangoma.plugins.metadata.acoustid import AcoustIDPlugin
    from patangoma.plugins.metadata.deezer import DeezerPlugin
    from patangoma.plugins.metadata.discogs import DiscogsPlugin
    from patangoma.plugins.metadata.itunes import ITunesPlugin
    from patangoma.plugins.metadata.lyrics import LyricsPlugin
    from patangoma.plugins.metadata.musicbrainz import MusicBrainzPlugin
    from patangoma.plugins.metadata.spotify import SpotifyPlugin

    registry = PluginRegistry()

    # Built-in capability plugins
    builtins: list[Plugin] = [
        # Metadata
        MusicBrainzPlugin(),
        DeezerPlugin(),
        SpotifyPlugin(),
        DiscogsPlugin(),
        ITunesPlugin(),
        AcoustIDPlugin(),
        LyricsPlugin(),
        # Media tools
        ChromaprintMediaPlugin(),
        FFmpegMediaPlugin(),
        # Artwork
        CoverArtArchivePlugin(),
        # Downloads
        Aria2DownloadPlugin(),
        YtDlpDownloadPlugin(),
        # Exporters & Importers
        JSONExporterPlugin(),
        CSVExporterPlugin(),
        M3UPlaylistExporterPlugin(),
        JSONImporterPlugin(),
    ]

    for p in builtins:
        registry.register(p)

    return registry
