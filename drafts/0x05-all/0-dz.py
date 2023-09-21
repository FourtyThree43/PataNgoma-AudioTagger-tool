import deezer
import json
import logging
from functools import lru_cache
from typing import Optional, List, Dict, Any


class DeezerClient:
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

    def flatten_dict(self,
                     input_dict: Dict[str, Any],
                     parent_key="",
                     separator="."):
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

    dz = DeezerClient()
    dz_data = dz.search_track(track_title=tr.title,
                              artist_name=tr.artist,
                              album_title=None)
    if dz_data:
        choices = []

        for idx, rec in enumerate(dz_data, start=1):
            flt_rec = dz.flatten_dict(rec)

            choice_item = {
                "name":
                f"{idx}. Title: {flt_rec['title']} - {flt_rec['artist.name']}\n"
                +
                f"       Album: {flt_rec['album.title']} - {flt_rec['album.type']}\n",
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

            track_data = dz.get_track_by_id(selected_track["id"])
            album_data = dz.get_album_by_id(selected_track["album"]["id"])
            artist_data = dz.get_artist_by_id(selected_track["artist"]["id"])

            # del track_data["available_countries"]
            # del album_data["tracks"]
            # flt_Tdata = dz.flatten_dict(track_data)
            # flt_Adata = dz.flatten_dict(album_data)

            # trans_Tdata = dz.translate_deezer_result(flt_Adata)
            # trans_Adata = dz.translate_deezer_result(flt_Adata)

            # dz.dump_res(flt_Adata)

            try:
                import requests
                import imgcat

                print("Fetching track info...")

                trkInfo = dz.deezTrack(track_data)
                albInfo = dz.deezAlbum(album_data)

                try:
                    art = requests.get(albInfo.cover).content
                    print("Album cover fetched")
                    imgcat.imgcat(art)

                except Exception as e:
                    print(f"An error occurred while fetching album cover: {e}")
                    art = None

                metadata_mapping = {
                    "album": albInfo.title,
                    "albumartist": albInfo.artist["name"],
                    "albumtype": albInfo.type,
                    "artist": trkInfo.artist["name"],
                    "artists_credit": [co.name for co in trkInfo.contributors],
                    "date": albInfo.release_date,
                    "disc": trkInfo.disk_number,
                    "genres": [genre["name"] for genre in albInfo.genres],
                    "art": art,
                    "isrc": trkInfo.isrc,
                    "label": albInfo.label,
                    "title": trkInfo.title,
                    "track": trkInfo.track_position,
                    "tracktotal": albInfo.nb_tracks,
                    "url": trkInfo.link,
                }

                update("../music/track", metadata_mapping)

            except AttributeError as e:
                print(f"An error occurred: {e}")

    else:
        print("Track not found")
