"""Canonical genre taxonomy and normalization service."""

from __future__ import annotations

import re
from typing import ClassVar

from pydantic import BaseModel

_GENRE_TAXONOMY_MAP: dict[str, str] = {
    # Hip-Hop / Rap
    "hip hop": "Hip-Hop",
    "hiphop": "Hip-Hop",
    "hip-hop": "Hip-Hop",
    "rap": "Hip-Hop",
    "hip hop/rap": "Hip-Hop",
    "hip hop rap": "Hip-Hop",
    "trap": "Hip-Hop",
    # R&B / Soul
    "r&b": "R&B",
    "rnb": "R&B",
    "r and b": "R&B",
    "contemporary r&b": "R&B",
    "soul": "Soul",
    "neo-soul": "Neo-Soul",
    # Electronic
    "electronic": "Electronic",
    "electronica": "Electronic",
    "edm": "EDM",
    "house": "House",
    "deep house": "House",
    "techno": "Techno",
    "trance": "Trance",
    "synthpop": "Synthpop",
    "synth pop": "Synthpop",
    "synth-pop": "Synthpop",
    "drum and bass": "Drum & Bass",
    "drum & bass": "Drum & Bass",
    "dnb": "Drum & Bass",
    # Rock / Alternative
    "rock": "Rock",
    "alt rock": "Alternative Rock",
    "alternative rock": "Alternative Rock",
    "alternative": "Alternative",
    "indie rock": "Indie Rock",
    "indie": "Indie",
    "hard rock": "Hard Rock",
    "punk": "Punk",
    "punk rock": "Punk Rock",
    "metal": "Metal",
    "heavy metal": "Heavy Metal",
    # Pop
    "pop": "Pop",
    "dance pop": "Dance-Pop",
    "dance-pop": "Dance-Pop",
    "k-pop": "K-Pop",
    "kpop": "K-Pop",
    "j-pop": "J-Pop",
    "jpop": "J-Pop",
    "afropop": "Afropop",
    "afrobeats": "Afrobeats",
    "afrobeat": "Afrobeats",
    # Jazz / Classical / World
    "jazz": "Jazz",
    "classical": "Classical",
    "reggae": "Reggae",
    "dancehall": "Dancehall",
    "ambient": "Ambient",
    "folk": "Folk",
    "blues": "Blues",
    "country": "Country",
}


class GenreNormalizationResult(BaseModel):
    """Result of normalizing a track's genre tags."""

    raw_genre: str
    canonical_genre: str
    changed: bool


class GenreNormalizer:
    """Standardizes messy genre tags into clean canonical taxonomy categories."""

    _MAP: ClassVar[dict[str, str]] = _GENRE_TAXONOMY_MAP

    def __init__(self, custom_overrides: dict[str, str] | None = None) -> None:
        self._rules = {**self._MAP, **(custom_overrides or {})}

    def normalize(self, raw_genre: str | None) -> GenreNormalizationResult:
        """Normalize a single genre tag string."""
        if not raw_genre or not raw_genre.strip():
            return GenreNormalizationResult(
                raw_genre="", canonical_genre="", changed=False
            )

        cleaned = raw_genre.strip()
        lookup_key = re.sub(r"[\s/_.-]+", " ", cleaned.lower()).strip()

        # Exact normalized match in taxonomy map
        if lookup_key in self._rules:
            canon = self._rules[lookup_key]
            return GenreNormalizationResult(
                raw_genre=cleaned,
                canonical_genre=canon,
                changed=cleaned != canon,
            )

        # Title-case fallback
        canon = " ".join(word.capitalize() for word in cleaned.split())
        return GenreNormalizationResult(
            raw_genre=cleaned,
            canonical_genre=canon,
            changed=cleaned != canon,
        )
