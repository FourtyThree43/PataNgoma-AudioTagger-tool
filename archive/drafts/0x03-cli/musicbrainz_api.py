from musicbrainzngs import musicbrainz as mb


class MusicBrainAPI:
    """
    class that deals with the sourcing info from musicbrainzngs
    """

    def __init__(self) -> None:
        mb.set_useragent("PataNgoma", "0.1")
        mb.set_format('json')

        mb.search_labels.

    def search_album(self, album_title, artist_name):
        """
        Args:
            album_title: str
            artist_name: srt
        Return List: Search results form musicbrainzngs
        """
        try:
            result = mb.search_releases(
                query=f'release:"{album_title}" AND artist:"{artist_name}"')
            return result['release-list']
        except Exception as e:
            print(e)
            return []

    def search_artist(self, artist_name):
        """
        Args:
            artist_name: str
        Return List: Search results form musicbrainzngs
        """
        try:
            result = mb.search_artists(query=f'artist:"{artist_name}"')
            return result['artist-list']
        except Exception as e:
            print(e)
            return []

    def search_label(self, label_name):
        """
        Args:
            label_name: str
        Return List: Search results form musicbrainzngs
        """
        try:
            result = mb.search_labels(query=f'label:"{label_name}"')
            return result['label-list']
        except Exception as e:
            print(e)
            return []

    def search_recording(self, recording_title, artist_name):
        """
        Args:
            recording_title: str
            artist_name: str
        Return List: Search results form musicbrainzngs
        """
        try:
            result = mb.search_recordings(
                query=f'recording:"{recording_title}" AND artist:"{artist_name}"')
            return result['recording-list']
        except Exception as e:
            print(e)
            return []

