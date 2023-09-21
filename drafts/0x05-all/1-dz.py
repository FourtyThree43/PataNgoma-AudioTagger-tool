import deezer
import json
import logging
from functools import lru_cache
from typing import Optional, List, Dict, Any
from datetime import datetime


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

    def translate_deezer_result(self, result: Dict[str,
                                                   Any]) -> Dict[str, Any]:
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
            # "id": "dz_TrackID",
            # "readable": True,
            "title": "title",
            "isrc": "isrc",
            "link": "url",
            # "duration": "length",
            "track_position": "track",
            "disk_number": "disc",
            "release_date": "date",
            # "preview": "url/.mp3",
            # "contributors[0].id": 4750006,
            # "contributors[0].name": "artist_credit",
            # "contributors[1].name": "artists_credit",
            # "md5_image": "image-hash",
            # "artist.id": "dz_ArtistID",
            "artist.name": "artist",
            # "album.id": "dz_AlbumID",
            "album.title": "album",
            # "album.link": "url",
            # "album.cover": "url/image",
            # "album.cover_big": "url/image",
            # "album.cover_xl": "url/image",
            # "album.md5_image": "image-hash",
            "album.release_date": "date",
            "album.type": "albumtype",
        }

        translated_data = {}

        for flattened_key, value in result.items():
            if flattened_key in reverse_mapping:
                mediafile_key = reverse_mapping[flattened_key]
                if mediafile_key == "date" and not isinstance(value, datetime):
                    try:
                        value = datetime.strptime(value, "%Y-%m-%d").date()
                    except ValueError:
                        try:
                            value = datetime.strptime(value, "%Y").date()
                        except ValueError:
                            print(f"Cannot convert {value} to datetime.date")
                        continue

                translated_data[mediafile_key] = value

        return translated_data

    def dump_res(self, results: Dict[str, Any]) -> None:
        json_results = json.dumps(results, indent=4)
        print(json_results)

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

    print(f"Searched Track: {tr.title}, {tr.artist}, {tr.album}")

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
            client = deezer.Client()

            selected_track = dz_data[selection - 1]

            track_data = client.get_track(selected_track["id"])
            trkInfo = deezer.Track(client, track_data.__dict__)

            album_data = trkInfo.get_album()
            albInfo = deezer.Album(client, album_data)

            metadata_mapping = {
                "album": f"{albInfo.title}",
                "albumartist": f"{albInfo.artist}",
                "albumtype": f"{albInfo.type}",
                "artist": f"{trkInfo.artist}",
                "artists_credit": f"{trkInfo.contributors}",
                "date": f"{albInfo.release_date}",
                "disc": f"{trkInfo.disk_number}",
                "genres": f"{albInfo.genres}",
                "images": f"{albInfo.cover_xl}",
                "isrc": f"{trkInfo.isrc}",
                "label": f"{albInfo.label}",
                "title": f"{trkInfo.title}",
                "track": f"{trkInfo.track_position}",
                "tracktotal": f"{albInfo.nb_tracks}",
                "url": f"{trkInfo.link}",
                "year": f"{albInfo.release_date}",
            }

            # del track_data["available_countries"]
            # flt_Tdata = dz.flatten_dict(track_data)
            # flt_Adata = dz.flatten_dict(album_data)

            # trans_data = dz.translate_deezer_result(flt_data)

            # dz.dump_res(flt_Adata)
            update("../music/track", metadata_mapping)

    else:
        print("Track not found")
