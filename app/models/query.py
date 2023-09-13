from app.api.mb import MusicBrainzAPI
from app.models.data_store import DataStore
from app.models.track import TrackInfo
from cachetools import TTLCache
import logging
import re

from app.models.id_extractor import (
    spotify_id_regex,
    deezer_id_regex,
    beatport_id_regex,
    extract_discogs_id_regex,
)


class Query:
    """ Class that handles the query to the MusicBrainzAPI """

    def __init__(self, track_info: TrackInfo, data_store: DataStore):

        self.track_info = track_info
        self.mb_api = MusicBrainzAPI()
        self.data_store = data_store
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        self.cache = TTLCache(maxsize=100, ttl=3600)  # Cache for 1 hour

    def fetch_musicbrainz_data(self):
        # Extract title and artist from TrackInfo
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
                flatted_result = self.flatten_dict(result[0])
                translated_data = self.mb_api.translate_mb_result(flatted_result)
                self.data_store.add_metadata("musicbrainz", result[0])
                self.cache[cache_key] = flatted_result

                return translated_data
                # return self.mb_api.translate_mb_result(result[0])
        except Exception as e:
            print(f"Error searching track on MusicBrainz: {str(e)}")

        return None

    def flatten_dict(self, input_dict, parent_key='', separator='.'):
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

    def translate_query_params(self, query_params):
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
            "my_param1": "mb_field1",
            "my_param2": "mb_field2",
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

    def store_metadata(self, source, data: dict):
        """Store the metadata in the DataStore"""
        self.data_store.add_metadata(source, data)

    def search_by_spotify_id(self, text):
        """
        Search for items/albums by Spotify ID in the given text.
        Returns a list of matching items/albums.
        """
        spotify_id_matches = re.finditer(spotify_id_regex['pattern'], text)
        matching_ids = [match.group(spotify_id_regex['match_group']) for match in spotify_id_matches]
        # Use matching_ids to perform your query and return the results

    def search_by_deezer_id(self, text):
        """
        Search for items/albums by Deezer ID in the given text.
        Returns a list of matching items/albums.
        """
        deezer_id_matches = re.finditer(deezer_id_regex['pattern'], text)
        matching_ids = [match.group(deezer_id_regex['match_group']) for match in deezer_id_matches]
        # Use matching_ids to perform your query and return the results

    def search_by_beatport_id(self, text):
        """
        Search for items/albums by Beatport ID in the given text.
        Returns a list of matching items/albums.
        """
        beatport_id_matches = re.finditer(beatport_id_regex['pattern'], text)
        matching_ids = [match.group(beatport_id_regex['match_group']) for match in beatport_id_matches]
        # Use matching_ids to perform your query and return the results

    def search_by_discogs_id(self, text):
        """
        Search for items/albums by Discogs ID in the given text.
        Returns a list of matching items/albums.
        """
        discogs_id = extract_discogs_id_regex(text)
        if discogs_id is not None:
            # Use discogs_id to perform your query and return the results
            pass
