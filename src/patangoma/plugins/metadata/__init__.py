"""Metadata plugins package for PataNgoma."""

from patangoma.plugins.metadata.acoustid import (
    AcoustIDPlugin,
    AcoustIDProvider,
    find_fpcalc_binary,
    generate_chromaprint,
)
from patangoma.plugins.metadata.deezer import DeezerPlugin, DeezerProvider
from patangoma.plugins.metadata.discogs import DiscogsPlugin, DiscogsProvider
from patangoma.plugins.metadata.itunes import ITunesPlugin, ITunesProvider
from patangoma.plugins.metadata.lyrics import LyricsPlugin, LyricsProvider
from patangoma.plugins.metadata.musicbrainz import (
    MusicBrainzPlugin,
    MusicBrainzProvider,
)
from patangoma.plugins.metadata.spotify import SpotifyPlugin, SpotifyProvider

__all__ = [
    "AcoustIDPlugin",
    "AcoustIDProvider",
    "DeezerPlugin",
    "DeezerProvider",
    "DiscogsPlugin",
    "DiscogsProvider",
    "ITunesPlugin",
    "ITunesProvider",
    "LyricsPlugin",
    "LyricsProvider",
    "MusicBrainzPlugin",
    "MusicBrainzProvider",
    "SpotifyPlugin",
    "SpotifyProvider",
    "find_fpcalc_binary",
    "generate_chromaprint",
]
