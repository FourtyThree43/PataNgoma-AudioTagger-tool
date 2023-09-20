import deezer
import json
import logging
from functools import lru_cache
from typing import Optional, List, Dict, Any
from InquirerPy import inquirer


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

    def translate_deezer_result(self, result):
        """
        Translate Deezer result to a format that of MediaFile.

        Parameters
        ----------
        result : dict
            The Deezer result to translate.

        Returns
        -------
        dict
            The translated result.
        """
        reverse_mapping = {
            # "id": 1136178852,
            # "readable": True,
            "title": "Catch A Vibe",
            "title_short": "Catch A Vibe",
            # "title_version": "",
            # "isrc": "US23A1515295",
            "link": "url2",
            "track_position": 1,
            "disk_number": 1,
            "release_date": "2020-12-04",
            # "preview": "url/.mp3",
            # "contributors[0].id": 4750006,
            "contributors[0].name": "Karun",
            "contributors[1].name": "MOMBRU",
            # "md5_image": "2a0c26b18943ed8c1fe0831efe56089b",
            "artist.id": 4750006,
            "artist.name": "Karun",
            "album.id": 185087412,
            "album.title": "Catch A Vibe",
            # "album.link": "url",
            # "album.cover": "url/image",
            # "album.cover_big": "url/image",
            # "album.cover_xl": "url/image",
            # "album.md5_image": "image-hash",
            "album.release_date": "2020-12-04",
            "album.type": "album",
        }

        translated_data = {}

        for key, value in result.items():
            if key in reverse_mapping:
                translated_key = reverse_mapping[key]
                translated_data[translated_key] = value

        return translated_data

    def dump_res(self, results: Dict[str, Any]) -> None:
        json_results = json.dumps(results, indent=4)
        print(json_results)

    def flatten_dict(self,
                     input_dict: Dict[str, Any],
                     parent_key='',
                     separator='.'):
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

    dz = DeezerClient()
    dz_data = dz.search_track(track_title="Breathe",
                              artist_name="Pink Floyd",
                              album_title="The Dark Side of the Moon")
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
                idx
            }
            choices.append(choice_item)

        selection = inquirer.select(
            message="Select a track:",
            choices=choices,
            amark="✔",
            default=1,
            instruction="Use arrow keys to navigate, press Enter to select",
            max_height="70%").execute()

        if selection:
            selected_track = dz_data[selection - 1]
            print(selected_track["id"])
            track_data = dz.get_track_by_id(selected_track.get("id"))
            del track_data["available_countries"]
            flt_track = dz.flatten_dict(selected_track)
            dz.dump_res(flt_track)

    else:
        print("Track not found")
