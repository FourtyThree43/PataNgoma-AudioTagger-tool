from functools import lru_cache
import logging
import musicbrainzngs as mb


class MusicBrainzAPI:

    def __init__(self, response_format="xml"):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

        self.set_user_agent()
        self.set_format(response_format)

    def set_user_agent(self,
                       app="PataCLI",
                       version="1.0",
                       contact="pata@example.com"):
        """Set the user agent for API requests."""
        mb.set_useragent(app=app, version=version, contact=contact)

    def set_format(self, fmt="xml"):
        """Set the response format for API requests."""
        mb.set_format(fmt=fmt)

    @lru_cache(maxsize=None)
    def search_track(self, track_title, artist_name, query=None):
        try:
            query_params = {"artist": artist_name, "recording": track_title}

            if query:
                query_params.update(query)

            result = mb.search_recordings(**query_params)

            if "recording-list" in result:
                return result["recording-list"]
        except mb.WebServiceError as e:
            self.logger.error(
                f"Error searching track on MusicBrainz: {str(e)}")
        return []

    def translate_mb_result(self, flattened_data):
        """
        Translate flattened data back to MediaFile keys.
        """
        reverse_mapping = {
            'id': 'mbid',
            'ext:score': 'scores',
            'title': 'title',
            'length': 'length',
            'artist-credit[0].name': 'artist',
            'artist-credit[0].artist.id': 'artist-mbid',
            'artist-credit[0].artist.name': 'artist',
            'artist-credit[0].artist.sort-name': 'artist-sort',
            'artist-credit[1]': 'artist-credit-phrase',
            'release-list[0].id': 'album-mbid',
            'release-list[0].title': 'album',
            'release-list[0].status': 'albumstatus',
            'release-list[0].artist-credit[0].name': 'albumartist',
            'release-list[0].artist-credit[0].artist.id': 'albumartist-mbid',
            'release-list[0].artist-credit[0].artist.name': 'albumartist',
            'release-list[0].artist-credit[0].artist.sort-name': 'albumartist-sort',
            'release-list[0].release-group.id': 'album-mbid',
            'release-list[0].release-group.type': 'albumtype',
            'release-list[0].release-group.title': 'album',
            'release-list[0].release-group.primary-type': 'albumtype',
            'release-list[0].date': 'year',
            'release-list[0].country': 'country',
            'release-list[0].release-event-list[0].date': 'year',
            'release-list[0].release-event-list[0].area.id': 'country-mbid',
            'release-list[0].release-event-list[0].area.name': 'country',
            'release-list[0].release-event-list[0].area.sort-name': 'country-sort',
            # 'release-list[0].release-event-list[0].area.iso-3166-1-code-list[0]': 'country',
            'release-list[0].medium-list[0].position': 'discnumber',
            'release-list[0].medium-list[0].format': 'media',
            'release-list[0].medium-list[0].track-list[0].id': 'track-mbid',
            'release-list[0].medium-list[0].track-list[0].number': 'tracknumber',
            'release-list[0].medium-list[0].track-list[0].title': 'title',
            'release-list[0].medium-list[0].track-list[0].length': 'length',
            'release-list[0].medium-list[0].track-list[0].track_or_recording_length': 'length',
            'release-list[0].medium-list[0].track-count': 'track',
            'release-list[0].medium-track-count': 'track',
            'release-list[0].medium-count': 'disc',
            'release-list[0].artist-credit-phrase': 'artist-credit-phrase',
            'artist-credit-phrase': 'artist',
        }

        translated_data = {}

        for flattened_key, value in flattened_data.items():
            if flattened_key in reverse_mapping:
                mediafile_key = reverse_mapping[flattened_key]
                translated_data[mediafile_key] = value

        return translated_data
