"""MusicBrainz provider re-export bridge for backward compatibility."""

from patangoma.plugins.metadata.musicbrainz import (
    MusicBrainzPlugin,
    MusicBrainzProvider,
)

__all__ = ["MusicBrainzPlugin", "MusicBrainzProvider"]
