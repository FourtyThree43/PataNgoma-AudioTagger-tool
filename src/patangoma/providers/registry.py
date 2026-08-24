"""Provider registry for discovering and instantiating metadata providers."""

from __future__ import annotations

from collections.abc import Callable, Sequence

from patangoma.domain.exceptions import ProviderError
from patangoma.providers.acoustid import AcoustIDProvider
from patangoma.providers.base import MetadataProvider
from patangoma.providers.deezer import DeezerProvider
from patangoma.providers.discogs import DiscogsProvider
from patangoma.providers.itunes import ITunesProvider
from patangoma.providers.lyrics import LyricsProvider
from patangoma.providers.musicbrainz import MusicBrainzProvider
from patangoma.providers.spotify import SpotifyProvider

_PROVIDER_FACTORIES: dict[str, Callable[[], MetadataProvider]] = {
    "musicbrainz": lambda: MusicBrainzProvider(),
    "deezer": lambda: DeezerProvider(),
    "spotify": lambda: SpotifyProvider(),
    "itunes": lambda: ITunesProvider(),
    "discogs": lambda: DiscogsProvider(),
    "acoustid": lambda: AcoustIDProvider(),
    "lyrics": lambda: LyricsProvider(),
}


def get_provider(name: str) -> MetadataProvider:
    """Get metadata provider instance by name."""
    norm_name = name.lower().strip()
    factory = _PROVIDER_FACTORIES.get(norm_name)
    if not factory:
        available = ", ".join(_PROVIDER_FACTORIES.keys())
        raise ProviderError(
            f"Unknown metadata provider '{name}'. Available: {available}"
        )
    return factory()


def get_available_providers() -> Sequence[str]:
    """List names of all supported metadata providers."""
    return tuple(_PROVIDER_FACTORIES.keys())
