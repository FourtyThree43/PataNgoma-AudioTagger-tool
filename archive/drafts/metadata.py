from mediafile import MediaFile

class TrackInfo:
    def __init__(self, file_path):
        self.file_path = file_path
        self.load_metadata()

    def load_metadata(self):
        media = MediaFile(self.file_path)
        self.title = media.title
        self.artist = media.artist
        self.album = media.album
        self.duration = media.length
        # Add more attributes as needed

class AlbumInfo:
    def __init__(self, album_name, artist_name):
        self.album_name = album_name
        self.artist_name = artist_name
        self.tracks = []

    def add_track(self, track_info):
        self.tracks.append(track_info)
        

    # You can add more methods and attributes as needed
