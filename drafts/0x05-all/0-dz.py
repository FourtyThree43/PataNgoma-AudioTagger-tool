import requests
from imgcat import imgcat
import deezer
import logging
from functools import lru_cache
from typing import Optional, List, Dict, Any
from cachetools import TTLCache
from data_store import DataStore
from mb import MusicBrainzAPI
from tags import TrackInfo


class Query:
    """ Class that handles the query to the MusicBrainzAPI """

    def __init__(self, track_info: TrackInfo, data_store: DataStore):

        self.track_info = track_info
        self.mb_api = MusicBrainzAPI()
        self.dz_api = DeezerAPI()
        self.data_store = data_store
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        self.cache = TTLCache(maxsize=100, ttl=3600)  # Cache for 1 hour
        self.fetched_data = None

    def fetch_musicbrainz_data(self, title: Optional[str],
                               artist: Optional[str]) -> List[Dict[str, Any]]:
        # Extract title and artist from TrackInfo
        if not (self.track_info.title and self.track_info.artist):
            title = self.track_info.title
            artist = self.track_info.artist

        cache_key = (title, artist)

        if cache_key in self.cache:
            self.logger.info("Using cached result for MusicBrainz query.")
            return self.cache[cache_key]

        try:
            # qparams = {}

            # to implement later: Translates the query params
            # form meadifile fields to mb fields

            # qparams = self.translate_query_params(
            #     self.track_info.get_params()) if self.track_info else {}

            result = self.mb_api.search_track(title, artist)

            if result:
                translated_data_list = []
                self.cache[cache_key] = result

                for idx, res in enumerate(result, start=1):
                    flat_result = self.flatten_dict(res)
                    translated_data = self.mb_api.translate_mb_result(
                        flat_result)
                    translated_data_list.append(translated_data)
                    self.store_metadata("musicbrainz", translated_data)

                return translated_data_list
                # return self.mb_api.translate_mb_result(result[0])
        except Exception as e:
            print(f"Error searching track on MusicBrainz: {str(e)}")

        return []

    def fetch_deezer_data(self, title: Optional[str], artist: Optional[str],
                          album: Optional[str]) -> List[Dict[str, Any]]:
        """ Searches for tracks in Deezer's database based on the given
            parameters & returns a list of Track instances.

            Parameters
            ----------
            title : str, optional
                The title of the track to search for, if applicable.
            artist : str, optional
                The name of the artist to search for, if applicable.
            album : str, optional
                The title of the album to search for, if applicable.

            Returns
            -------
            List[Track]
                A list of Track instances matching the search criteria.
                An empty list if an error occurs or no matches are found.
        """
        try:
            results = self.dz_api.search_track(title, artist, album)

            if results:
                data_list: List[Dict[str, Any]] = []

                for idx, res in enumerate(results, start=1):
                    data_list.append(res)
                    self.store_metadata("deezer", res)

                return data_list

        except Exception as e:
            print(f"Error searching track on Deezer: {str(e)}")

        return []

    def fetch_spotify_data(self):
        pass

    def flatten_dict(self,
                     input_dict: Dict[str, Any],
                     parent_key='',
                     separator='.') -> Dict[str, Any]:
        """
        Recursively flatten a nested dict and convert keys to dot notation.
        """
        flat_dict = {}

        for key, value in input_dict.items():
            new_key = f"{parent_key}{separator}{key}" if parent_key else key

            if isinstance(value, dict):
                flat_dict.update(self.flatten_dict(value, new_key, separator))
            elif isinstance(value, list):
                for i, item in enumerate(value):
                    if isinstance(item, dict):
                        flat_dict.update(
                            self.flatten_dict(item, f"{new_key}[{i}]",
                                              separator))
                    else:
                        flat_dict[f"{new_key}[{i}]"] = item
            else:
                flat_dict[new_key] = value

        return flat_dict

    def translate_query_params(self,
                               query_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Translate query parameters to match MusicBrainz fields.

        Args:
            query_params (dict): The query parameters to translate.

        Returns:
            dict: Translated query parameters.
        """
        mb_query_params = {}

        # Define a mapping between your parameters and MusicBrainz fields
        parameter_mapping = {
            "album": "releases",
            # "my_param2": "mb_field2",
            # Add more mappings as needed
        }

        # Translate query parameters using the mapping
        for key, value in query_params.items():
            if key in parameter_mapping:
                mb_key = parameter_mapping[key]
                mb_query_params[mb_key] = value

        return mb_query_params

    def fetch_DataStore_data(self, source=None):
        """
        Retrieve metadata from the DataStore based on the source or
        return all the metadata if no source is specified
        """
        if source is None:
            data = self.data_store.get_all_metadata()
        else:
            data = self.data_store.get_metadata(source)

        if data:
            self.fetched_data = data

        return data

    def store_metadata(self, source, data: Dict[str, Any]):
        """Store the metadata in the DataStore"""
        self.data_store.add_metadata(source, data)


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
    def search_track(
            self,
            track_title: str,
            artist_name: str,
            album_title: Optional[str] = None) -> List[Dict[str, Any]]:
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

    def get_album_by_isrc(self, isrc: str) -> Dict[str, Any]:
        """
        Retrieves an album from Deezer's database using its unique ISRC code.

        Parameters
        ----------
        isrc : str
            The ISRC code for the album.

        Returns
        -------
        dict or None
            If the album is found, returns a dict containing the album data.
            If an error occurs (e.g., the ISRC code is not valid), returns None.
        """
        try:
            results = self.client.get_album(isrc)

            return results.as_dict()

        except Exception as e:
            self.logger.error(f"Error searching album on Deezer: {str(e)}")

            return {}

    def get_artist_by_isrc(self, isrc: str) -> Dict[str, Any]:
        """
        Retrieves an artist from Deezer's database using its unique ISRC code.

        Parameters
        ----------
        isrc : str
            The ISRC code for the artist.

        Returns
        -------
        dict or None
            If the artist is found, returns a dict containing the artist data.
            If an error occurs (e.g., the ISRC code is not valid), returns None.
        """
        try:
            results = self.client.get_artist(isrc)

            return results.as_dict()

        except Exception as e:
            self.logger.error(f"Error searching artist on Deezer: {str(e)}")

            return {}

    def get_album_by_upc(self, upc: str) -> Dict[str, Any]:
        """
        Retrieves an album from Deezer's database using its unique UPC code.

        Parameters
        ----------
        upc : str
            The UPC code for the album.

        Returns
        -------
        dict or None
            If the album is found, returns a dict containing the album data.
            If an error occurs (e.g., the UPC code is not valid), returns None.
        """
        try:
            results = self.client.get_album(upc)

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


if __name__ == "__main__":
    import click
    from InquirerPy import inquirer
    from tags import TrackInfo

    def update(file_path, updates):
        """Update metadata for a media file."""
        track = TrackInfo(file_path)
        md_pre_update = track.as_dict()

        track.batch_update_metadata(updates)

        if track.has_changed(track.as_dict(), md_pre_update):
            click.echo(f"Metadata changes for {track.metadata.filename}:")
            for key, value in track.as_dict().items():
                if key != "images" and md_pre_update[key] != value:
                    if key not in ("art", "lyrics"):
                        click.echo(f"{key}: {md_pre_update[key]} -> {value}")
                    elif key == "art":
                        click.echo(f"{'-' * 10} Original {'-' * 10}\n")
                        imgcat(md_pre_update[key], width=24, height=24)

                        click.echo(f"{'-' * 10} Updated {'-' * 10}\n")
                        imgcat(value, width=24, height=24)
                    else:
                        click.echo(
                            f"{key}: changed (diff too large to display)")

            if click.confirm("Do you want to save these changes?"):
                track.save()
                click.echo("Changes saved.")
            else:
                click.echo("Changes not saved.")
        else:
            click.echo("No changes to save.")

    tr = TrackInfo("../music/track")

    print(f"Searching Track...\n {tr.title}, {tr.artist}, {tr.album}")

    ds = DataStore()
    qy = Query(tr, ds)
    dz = DeezerAPI()
    dz_data = qy.fetch_deezer_data(title=tr.title, artist=tr.artist, album="")

    if dz_data:
        choices = []

        for idx, rec in enumerate(dz_data, start=1):
            choice_item = {
                "name":
                f"{idx}. Title: {rec['title']} - {rec['artist']['name']}\n" +
                f"       Album: {rec['album']['title']} - {rec['album']['type']}\n",
                "value":
                idx,
            }
            choices.append(choice_item)

        selection = inquirer.select(
            message="Select a track:",
            choices=choices,
            amark="✔",
            default=1,
            instruction="Use arrow keys to navigate, press Enter to select",
            max_height="70%",
        ).execute()

        if selection:
            selected_track = dz_data[selection - 1]

            print("Fetching track info...")

            track_data = dz.get_track_by_id(selected_track["id"])
            album_data = dz.get_album_by_id(selected_track["album"]["id"])

            try:
                metadata_mapping = dz.mapData(track_data, album_data)

                update("../music/track", metadata_mapping)

            except AttributeError as e:
                print(f"An error occurred: {e}")

    else:
        print("Track not found")
