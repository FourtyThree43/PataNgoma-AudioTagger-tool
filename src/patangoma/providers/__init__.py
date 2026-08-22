"""Metadata providers package."""

from patangoma.providers.base import MetadataProvider
from patangoma.providers.deezer import DeezerProvider
from patangoma.providers.musicbrainz import MusicBrainzProvider
from patangoma.providers.registry import get_available_providers, get_provider
from patangoma.providers.spotify import SpotifyProvider

__all__ = [
    "DeezerProvider",
    "MetadataProvider",
    "MusicBrainzProvider",
    "SpotifyProvider",
    "get_available_providers",
    "get_provider",
]
