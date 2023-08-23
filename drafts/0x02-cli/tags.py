# metadata.py
from mediafile import MediaFile
from typing import Optional

class BaseModel:
    def __init__(self, file_path):
        self.file = file_path
        self.metadata = MediaFile(file_path)

    def as_dict(self):
        return dict(self.metadata.as_dict())

    def show_all(self):
        print(f"Metadata of {self.file}:")
        for key, value in self.as_dict().items():
            print(f"{key}: {value}")

    def show_metadata(self):
        print(f"Metadata of {self.file}:")
        for key, value in self.as_dict().items():
            if value is not None:
                print(f"{key}: {value}")

    def update_metadata(self, updates):
        for update in updates:
            key, value = update.split("=")
            if hasattr(self.metadata, key):
                setattr(self.metadata, key, value)
            else:
                print(f"Invalid metadata field: {key}")

    def delete(self):
        self.metadata.delete()

    def save(self):
        self.metadata.save()


class TrackInfo(BaseModel):
    def __init__(self, file_path):
        super().__init__(file_path)
        self.load_metadata()

    def load_metadata(self):
        self.title: Optional[str] = None
        self.artist: Optional[str] = None
        self.album: Optional[str] = None
        self.genre: Optional[str] = None

        if self.metadata:
            self.title = self.metadata.title
            self.artist = self.metadata.artist
            self.album = self.metadata.album
            self.genre = self.metadata.genre
