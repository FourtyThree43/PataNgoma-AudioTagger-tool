import musicbrainzngs as mb


class MusicBrainzAPI:

    def __init__(self):
        mb.set_useragent(app="MyMusicApp",
                         version="1.0",
                         contact="pata@example.com")
        mb.set_format(fmt="xml")

    def search_track(self, track_title, artist_name, query=None):
        try:
            query_params = {"artist": artist_name, "recording": track_title}

            if query:
                query_params.update(query)

            result = mb.search_recordings(**query_params)

            if "recording-list" in result:
                return result["recording-list"]
        except mb.WebServiceError as e:
            print(f"Error searching track: {str(e)}")
        return []

    def translate_mb_result(self, recording):
        """
        Translates a MusicBrainz recording result dictionary into a dictionary.
        """
        translated_data = {}
        translated_data['title'] = recording.get("title", "")
        translated_data['artist'] = recording.get(
            "artist-credit", [{}])[0].get("artist", {}).get("name", "")
        translated_data['album'] = recording.get("release-list",
                                                 [{}])[0].get("title", "")
        translated_data['genre'] = recording.get("genre", "")
        translated_data['year'] = recording.get("release-list",
                                                [{}])[0].get("date", "")

        return translated_data
