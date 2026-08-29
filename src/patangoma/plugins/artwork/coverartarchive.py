"""CoverArtArchive artwork plugin."""

from __future__ import annotations

import logging
from typing import Any

import requests

from patangoma.plugins.contracts import ArtworkProviderPlugin, PluginCapability

logger = logging.getLogger(__name__)


class CoverArtArchivePlugin(ArtworkProviderPlugin):
    """Artwork search plugin fetching covers from Cover Art Archive."""

    def __init__(self, session: requests.Session | None = None) -> None:
        self._name = "coverartarchive"
        self._session = session or requests.Session()

    @property
    def id(self) -> str:
        return "coverartarchive"

    @property
    def name(self) -> str:
        return "Cover Art Archive"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def capabilities(self) -> set[PluginCapability]:
        return {PluginCapability.ARTWORK}

    def health(self) -> dict[str, Any]:
        return {
            "status": "HEALTHY",
            "provider": self.name,
            "version": self.version,
        }

    def initialize(self) -> None:
        pass

    def shutdown(self) -> None:
        pass

    def search_artwork(self, album: str, artist: str, limit: int = 5) -> list[str]:
        """Search artwork by querying MusicBrainz release and building CAA URLs."""
        try:
            import musicbrainzngs as mb

            res = mb.search_releases(release=album, artist=artist, limit=limit)
            releases = res.get("release-list", [])
            urls = []
            for rel in releases:
                rel_id = rel.get("id")
                if rel_id:
                    urls.append(
                        f"https://coverartarchive.org/release/{rel_id}/front-500"
                    )
            return urls
        except Exception as e:
            logger.debug("CoverArtArchive search failed: %s", e)
            return []
