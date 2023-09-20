from typing import Optional, List
from patangoma.base import BaseModel
from patangoma.track import TrackInfo


class AlbumInfo(BaseModel):

    def __init__(self, file_path, tracks: List[TrackInfo]):
        super().__init__(file_path)
        self.tracks = tracks
        self.load_metadata()

    def load_metadata(self):
        self.album: Optional[str] = None
        self.album_id: Optional[str] = None
        self.artist: Optional[str] = None
        self.artist_id: Optional[str] = None
        self.albumtype: Optional[str] = None
        self.year: Optional[int] = None
        # Add more attributes as needed

        if self.metadata:
            self.album = self.metadata.album
            self.album_id = self.metadata.mb_albumid
            self.artist = self.metadata.albumartist
            self.artist_id = self.metadata.mb_artistid
            self.year = self.metadata.year
            # Load other album-specific metadata attributes

    def add_track(self, track: TrackInfo):
        """Add a track to the album."""
        self.tracks.append(track)

    def show_tracks(self):
        """Show information about tracks in the album."""
        print(f"Tracks in the Album {self.album}:")
        for i, track in enumerate(self.tracks, start=1):
            print(f"Track {i}: {track.title}")

    def get_params(self):
        metadata: dict = self.as_dict()

        params = {}
        for key, value in metadata.items():
            if value is not None and key not in ("art", "title", "artist",
                                                 "lyrics", "images"):
                params[key] = value
        return params
