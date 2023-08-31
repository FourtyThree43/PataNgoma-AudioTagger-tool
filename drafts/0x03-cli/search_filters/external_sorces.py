from musicbrainzngs import musicbrainz as mb
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials


class DataStore:

    def __init__(self):
        self.metadata = {}

    def add_metadata(self, source: str, data: dict):
        """Add metadata from an external source to the datastore."""
        if source not in self.metadata:
            self.metadata[source] = []
        self.metadata[source].append(data)

    def get_metadata(self, source: str):
        """Get metadata from a specific external source."""
        return self.metadata.get(source, [])

    def search_metadata(self, query: str):
        """Search for metadata across all sources."""
        results = []
        for source, data in self.metadata.items():
            for item in data:
                if query.lower() in item['title'].lower():
                    results.append(item)
        return results


class MusicBrainAPI:
    """
    Class that deals with sourcing information from MusicBrainzNGs.
    """

    def __init__(self, app_name, app_version, app_contact):
        mb.set_useragent(app_name, app_version, app_contact)

    def search_artist(self, artist_name: str):
        """Search for an artist by name."""
        result = mb.search_artists(artist=artist_name)
        return result

    def search_release(self, release_title: str):
        """Search for a release by title."""
        result = mb.search_releases(release=release_title)
        return result

    def search_recording(self, recording_title: str):
        """Search for a recording by title."""
        result = mb.search_recordings(recording=recording_title)
        return result


class SpotifyAPI:
    """
    Class that deals with sourcing information from the Spotify API.
    """

    def __init__(self, client_id, client_secret):
        auth_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
        self.sp = spotipy.Spotify(auth_manager=auth_manager)

    def search_track(self, track_name: str):
        """Search for a track by name."""
        result = self.sp.search(q='track:' + track_name, type='track')
        return result

    def search_artist(self, artist_name: str):
        """Search for an artist by name."""
        result = self.sp.search(q='artist:' + artist_name, type='artist')
        return result

    def search_album(self, album_name: str):
        """Search for an album by name."""
        result = self.sp.search(q='album:' + album_name, type='album')
        return result
