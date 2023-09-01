from data_store import DataStore
from mb import MusicBrainzAPI
from tags import TrackInfo


class Query:
    """ Class that handles the query to the MusicBrainzAPI """

    def __init__(self, track_info: TrackInfo, data_store: DataStore):

        self.track_info = track_info
        self.mb_api = MusicBrainzAPI()
        self.data_store = data_store

    def fetch_musicbrainz_data(self):
        try:
            # Extract title and artist from TrackInfo
            title = self.track_info.title
            artist = self.track_info.artist

            qparams = {}

            # to implement later: Translates the query params
            # form meadifile fields to mb fields

            # qparams = self.translate_query_params(
            #     self.track_info.get_params()) if self.track_info else {}

            result = self.mb_api.search_track(title, artist, qparams)

            if result:
                translated_result = self.mb_api.translate_mb_result(result[0])
                self.data_store.add_metadata("musicbrainz", result[0])
                return translated_result
                # return self.mb_api.translate_mb_result(result[0])
        except Exception as e:
            print(f"Error searching track on MusicBrainz: {str(e)}")

        return None

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

    def fetch_DataStore_data(self, source):
        """Retrieve metadata from the DataStore based on the source"""
        data = self.data_store.get_metadata(source)

        if data:
            self.fetched_data = data

        return data

    def store_metadata(self, source, data: dict):
        """Store the metadata in the DataStore"""
        self.data_store.add_metadata(source, data)
