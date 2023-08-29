# metadata.py
from mediafile import MediaFile
from imgcat import imgcat
import PIL
from typing import Optional


class BaseModel:

    def __init__(self, file_path):
        """Initialize a new instance of the BaseModel class."""
        self.file = file_path
        self.metadata = MediaFile(file_path)

    def as_dict(self):
        """Return a dictionary representation of the metadata."""
        return dict(self.metadata.as_dict())

    def show_all_metadata(self):
        """Print all metadata for {self.metadata.filename}."""
        print(f"All metadata of {self.metadata.filename}:\n")
        for key, value in self.as_dict().items():
            if key not in ("art", "images", "lyrics"):
                print(f"{key}: {value}")
            elif key == "art":
                print(key + ": ")
                imgcat(value)
            elif key == "images":
                print(key + ": ")
                for image in value:
                    imgcat(image.data)
            elif key == "lyrics":
                print(f"{key}: <LYRICS>")

    def show_existing_metadata(self):
        """Print non-empty non-binary metadata for {self.metadata.filename}."""
        print(f"Existing Metadata of {self.metadata.filename}:\n")
        for key, value in self.as_dict().items():
            if value is not None:
                if key not in ("art", "images", "lyrics"):
                    print(f"{key}: {value}")
                elif key == "art":
                    print(key + ": ")
                    imgcat(value)
                elif key == "images":
                    print(key + ": ")
                    for image in value:
                        imgcat(image.data)
                elif key == "lyrics":
                    print(f"{key}: <LYRICS>")

    def show_missing_metadata(self):
        """Print missing metadata for {self.metadata.filename}."""
        print(f"Missing Metadata of {self.metadata.filename}:\n")
        for key, value in self.as_dict().items():
            if value is None:
                print(f"{key}")

    def update_metadata(self, updates):
        """Update metadata for {self.metadata.filename}."""
        for update in updates:
            key, value = update.split("=")
            if hasattr(self.metadata, key):
                setattr(self.metadata, key, value)
            else:
                print(f"Invalid metadata field: {key}")

    def delete(self):
        """Delete metadata for {self.metadata.filename}."""
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
