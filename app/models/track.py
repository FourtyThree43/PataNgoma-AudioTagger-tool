from typing import Optional
from app.models.tags import BaseModel


class TrackInfo(BaseModel):
    """ TrackInfo class for track metadata """

    def __init__(self, file_path):
        super().__init__(file_path)
        self.title: Optional[str] = None
        self.artist: Optional[str] = None
        self.album: Optional[str] = None
        self.genre: Optional[str] = None

        if self.metadata:
            self.load_metadata()

    def load_metadata(self):
        if self.metadata:
            self.title = self.metadata.title
            self.artist = self.metadata.artist
            self.albumartist = self.metadata.albumartist
            self.album = self.metadata.album
            self.genre = self.metadata.genre
            self.year = self.metadata.year
            self.track = self.metadata.track
            self.tracktotal = self.metadata.tracktotal
            self.albumtype = self.metadata.albumtype

    def get_params(self):
        metadata: dict = self.as_dict()

        params = {}
        for key, value in metadata.items():
            if value is not None and key not in ("art", "title", "artist",
                                                 "lyrics", "images"):
                params[key] = value
        return params
