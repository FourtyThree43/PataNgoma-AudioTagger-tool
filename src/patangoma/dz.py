from functools import lru_cache
from typing import Optional, List, Dict, Any
import deezer
import imgcat
import logging
import requests


class DeezerAPI:
    """
    A class used to access Deezer's API
    ...

    Attributes
    ----------
    client : deezer.Client
        a deezer client object

    Methods
    -------
    search_track(artist_name: str, track_title: str, album_title: str):
        Searches for tracks in Deezer's database based on the given parameters
    get_track_by_id(track_id: int):
        Gets a track based on the given track_id
    dump_res(results: dict) -> None:
        Prints the results in a JSON format
    """

    def __init__(self):
        self.client = deezer.Client()
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

    @lru_cache(maxsize=128)
    def search_track(self, track_title: str, artist_name: str,
                     album_title: Optional[str]) -> List[Dict[str, Any]]:
        """
        Searches for tracks in Deezer's database based on the given parameters &
        returns a list of Track instances.

        Parameters
        ----------
        track_title : str
            The title of the track to search for.
        artist_name : str
            The name of the artist to search for.
        album_title : str, optional
            The title of the album to search for, if applicable.

        Returns
        -------
        List[Track]
            A list of Track instances matching the search criteria.
            Returns an empty list if an error occurs or no matches are found.
        """
        try:
            if album_title:
                query_params = 'track:"{}" artist:"{}" album:"{}"'.format(
                    track_title, artist_name, album_title)
            else:
                query_params = 'track:"{}" artist:"{}"'.format(
                    track_title, artist_name)

            results = self.client.search(query_params)

            return [result.as_dict() for result in results]

        except Exception as e:
            self.logger.error(f"Error searching track on Deezer: {str(e)}")
            return []

    def get_track_by_id(self, track_id: int) -> Dict[str, Any]:
        """
        Retrieves a track from Deezer's database using its unique track_id.

        Parameters
        ----------
        track_id : int
            The unique identifier for the track.

        Returns
        -------
        dict or None
            If the track is found, returns a dict containing the track data.
            If an error occurs (e.g., the track_id is not valid), returns None.
        """
        try:
            results = self.client.get_track(track_id)

            return results.as_dict()

        except Exception as e:
            self.logger.error(f"Error searching track on Deezer: {str(e)}")

            return {}

    def get_album_by_id(self, album_id: int) -> Dict[str, Any]:
        """
        Retrieves an album from Deezer's database using its unique album_id.

        Parameters
        ----------
        album_id : int
            The unique identifier for the album.

        Returns
        -------
        dict or None
            If the album is found, returns a dict containing the album data.
            If an error occurs (e.g., the album_id is not valid), returns None.
        """
        try:
            results = self.client.get_album(album_id)

            return results.as_dict()

        except Exception as e:
            self.logger.error(f"Error searching album on Deezer: {str(e)}")

            return {}

    def get_artist_by_id(self, album_id: int) -> Dict[str, Any]:
        """
        Retrieves an artist from Deezer's database using its unique album_id.

        Parameters
        ----------
        album_id : int
            The unique identifier for the album.

        Returns
        -------
        dict or None
            If the album is found, returns a dict containing the album data.
            If an error occurs (e.g., the album_id is not valid), returns None.
        """
        try:
            results = self.client.get_artist(album_id)

            return results.as_dict()

        except Exception as e:
            self.logger.error(f"Error searching album on Deezer: {str(e)}")

            return {}

    def deezTrack(self, track_data: Dict[str, Any]) -> deezer.Track:
        """
        Create a deezer.Track object from the given track_data.

        Parameters
        ----------
        track_data : dict
            The track data to use.

        Returns
        -------
        deezer.Track
            The deezer.Track object.
        """
        return deezer.Track(self.client, track_data)

    def deezAlbum(self, album_data: Dict[str, Any]) -> deezer.Album:
        """
        Create a deezer.Album object from the given album_data.

        Parameters
        ----------
        album_data : dict
            The album data to use.

        Returns
        -------
        deezer.Album
            The deezer.Album object.
        """
        return deezer.Album(self.client, album_data)

    def deezArtist(self, artist_data: Dict[str, Any]) -> deezer.Artist:
        """
        Create a deezer.Artist object from the given artist_data.

        Parameters
        ----------
        artist_data : dict
            The artist data to use.

        Returns
        -------
        deezer.Artist
            The deezer.Artist object.
        """
        return deezer.Artist(self.client, artist_data)

    def mapData(self, track_data: Dict[str, Any],
                album_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map the given track's data to a dict with the required fields.

        Parameters
        ----------
        track_data : dict
            The track data to use.

        album_data : dict
            The album data to use.

        Returns
        -------
        dict
            The mapped track data.
        """
        track = self.deezTrack(track_data)
        album = self.deezAlbum(album_data)

        album_art = self._fetch_art(album.cover_big)

        mapped_data = {
            "album": album.title,
            "albumartist": album.artist["name"],
            "albumtype": album.type,
            "artist": track.artist["name"],
            "artists": [co.name for co in track.contributors],
            "artists_credit": [co.name for co in track.contributors],
            "date": album.release_date,
            "disc": track.disk_number,
            "genres": [genre["name"] for genre in album.genres],
            "art": album_art,
            "isrc": track.isrc,
            "label": album.label,
            "title": track.title,
            "track": track.track_position,
            "tracktotal": album.nb_tracks,
            "url": track.link,
        }

        return mapped_data

    def _fetch_art(self, art_url: str) -> Optional[bytes]:
        """
        Fetch the album art for the given album.

        Parameters
        ----------
        art_url : str
            The album art url to fetch.

        Returns
        -------
        bytes or None
            The album art, if found.
            None, otherwise.
        """
        try:
            art = requests.get(art_url).content

        except Exception as e:
            print(f"An error occurred while fetching album cover: {e}")
            art = None

        return art
