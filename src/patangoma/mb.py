# mb.py
import musicbrainzngs as mb
import logging
from functools import lru_cache
from datetime import datetime


class MusicBrainzAPI:
    """Wrapper class for the MusicBrainz API.

    This class provides a wrapper around the MusicBrainz API to
    provide a more convenient interface for searching and retrieving
    track, artist, and album metadata.

    Attributes:
        logger (logging.Logger): The logger instance for this class.
        response_format (str): The format of the response from the API.
    """

    def __init__(self, response_format="xml"):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

        self.set_user_agent()
        self.set_format(response_format)

    def set_user_agent(self,
                       app="PataNgoma",
                       version="1.0",
                       contact="pata@example.com"):
        """Set the user agent for API requests.

        Args:
            app (str): The name of the application.
            version (str): The version of the application.
            contact (str): The contact email address of the application.
        """
        mb.set_useragent(app=app, version=version, contact=contact)

    def set_format(self, fmt="xml"):
        """Set the response format for API requests.

        Args:
            fmt (str): The format of the response from the API.
        """
        mb.set_format(fmt=fmt)

    @lru_cache(maxsize=None)
    def search_track(self, track_title: str, artist_name: str, query=None):
        """Search for a track on MusicBrainz.

        Args:
            track_title (str): The title of the track to search for.
            artist_name (str): The name of the artist of the track to search for.
            query (dict): Optional additional query parameters to pass to the API.

        Returns:
            list: A list of matching tracks.
        """
        try:
            query_params = {"artist": artist_name, "recording": track_title}

            if query:
                query_params.update(query)

            result = mb.search_recordings(**query_params, limit=10)

            if "recording-list" in result:
                return result["recording-list"]
        except mb.WebServiceError as e:
            self.logger.error(
                f"Error searching track on MusicBrainz: {str(e)}")
        return []

    def translate_mb_result(self, flattened_data):
        """
        Translate flattened data back to MediaFile keys

        Args:
            flattened_data (dict): flattened data from MusicBrainz

        Returns:
            dict: translated data
        """
        reverse_mapping = {
            "id": "mb_workid",
            "ext:score": "score",
            "title": "title",
            # "length": "length",
            "artist-credit[0].name": "artist",
            "artist-credit[0].artist.id": "mb_artistid",
            "artist-credit[0].artist.name": "artist",
            "artist-credit[0].artist.sort-name": "artist_sort",
            # "artist-credit[1]": ", Mombru",
            "release-list[0].id": "mb_albumid",
            "release-list[0].title": "album",
            "release-list[0].status": "albumstatus",
            "release-list[0].artist-credit[0].name": "albumartist",
            "release-list[0].artist-credit[0].artist.id": "mb_albumartistid",
            "release-list[0].artist-credit[0].artist.name": "albumartist",
            "release-list[0].artist-credit[0].artist.sort-name": "albumartist_sort",
            "release-list[0].release-group.id": "mb_albumid",
            "release-list[0].release-group.type": "albumtype",
            "release-list[0].release-group.title": "album",
            "release-list[0].release-group.primary-type": "albumtype",
            "release-list[0].date": "date",
            "release-list[0].country": "country",
            # "release-list[0].release-event-list[0].date": "date",
            # "release-list[0].release-event-list[0].area.id": "525d4e18-3d00-31b9-a58b-a146a916de8f",
            # "release-list[0].release-event-list[0].area.name": "[Worldwide]",
            # "release-list[0].release-event-list[0].area.sort-name": "[Worldwide]",
            # "release-list[0].release-event-list[0].area.iso-3166-1-code-list[0]": "XW",
            "release-list[0].medium-list[0].position": "track",
            "release-list[0].medium-list[0].format": "media",
            "release-list[0].medium-list[0].track-list[0].id": "mb_trackid",
            "release-list[0].medium-list[0].track-list[0].number": "track",
            "release-list[0].medium-list[0].track-list[0].title": "title",
            # "release-list[0].medium-list[0].track-list[0].length": "length",
            # "release-list[0].medium-list[0].track-list[0].track_or_recording_length": "length",
            "release-list[0].medium-list[0].track-count": "tracktotal",
            "release-list[0].medium-track-count": "tracktotal",
            "release-list[0].medium-count": "disc",
            # "release-list[0].artist-credit-phrase": "Karun",
            "artist-credit-phrase": "artist_credit"
        }

        translated_data = {}

        for flattened_key, value in flattened_data.items():
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
