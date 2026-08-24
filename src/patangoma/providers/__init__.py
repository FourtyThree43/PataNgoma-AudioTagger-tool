"""Metadata providers package."""

from patangoma.providers.acoustid import AcoustIDProvider
from patangoma.providers.base import MetadataProvider
from patangoma.providers.cache import (
    ProviderCache,
    cached_get_track,
    cached_search,
    default_provider_cache,
)
from patangoma.providers.deezer import DeezerProvider
from patangoma.providers.discogs import DiscogsProvider
from patangoma.providers.itunes import ITunesProvider
from patangoma.providers.lyrics import LyricsProvider
from patangoma.providers.musicbrainz import MusicBrainzProvider
from patangoma.providers.registry import get_available_providers, get_provider
from patangoma.providers.spotify import SpotifyProvider

__all__ = [
    "AcoustIDProvider",
    "DeezerProvider",
    "DiscogsProvider",
    "ITunesProvider",
    "LyricsProvider",
    "MetadataProvider",
    "MusicBrainzProvider",
    "ProviderCache",
    "SpotifyProvider",
    "cached_get_track",
    "cached_search",
    "default_provider_cache",
    "get_available_providers",
    "get_provider",
]
