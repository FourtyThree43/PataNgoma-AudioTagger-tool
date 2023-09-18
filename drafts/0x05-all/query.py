# query.py
from cachetools import TTLCache
from data_store import DataStore
from mb import MusicBrainzAPI
from tags import TrackInfo
import click
import logging


class Query:
    """ Class that handles the query to the MusicBrainzAPI """

    def __init__(self, track_info: TrackInfo, data_store: DataStore):

        self.track_info = track_info
        self.mb_api = MusicBrainzAPI()
        self.data_store = data_store
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        self.cache = TTLCache(maxsize=100, ttl=3600)  # Cache for 1 hour
        self.fetched_data = None

    def fetch_musicbrainz_data(self, title=None, artist=None):
        # Extract title and artist from TrackInfo
        if not (self.track_info.title and self.track_info.artist):
            title = self.track_info.title
            artist = self.track_info.artist
        # else:
        #     click.secho("Error: Missing title or artist", fg="red")
        #     exit(1)

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
                    translated_data = self.mb_api.translate_mb_result(flat_result)
                    translated_data_list.append(translated_data)
                    self.store_metadata("musicbrainz", translated_data)

                return translated_data_list
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
                            self.flatten_dict(item, f"{new_key}[{i}]", separator))
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

    def store_metadata(self, source, data: dict):
        """Store the metadata in the DataStore"""
        self.data_store.add_metadata(source, data)
