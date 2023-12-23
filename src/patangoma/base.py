from difflib import get_close_matches
from imgcat import imgcat
from mediafile import MediaFile


class BaseModel:
    """ A class that represents a base model for the application. """
    ART_METADATA = "art"
    IMAGES_METADATA = "images"
    LYRICS_METADATA = "lyrics"

    def __init__(self, file_path):
        self.file = file_path
        try:
            self.metadata = MediaFile(file_path)
        except Exception as e:
            print(f"Error loading metadata from {file_path}: {str(e)}")
            exit(1)

    def as_dict(self):
        """Return metadata as a dictionary."""
        try:
            return dict(self.metadata.as_dict())
        except Exception as e:
            print(f"Error converting metadata to dictionary: {str(e)}")
            return {}

    # Metadata Display Methods
    def show_all_metadata(self):
        """Print all metadata for {self.metadata.filename}."""
        metadata = self.as_dict()
        self._display_metadata(metadata)

    def show_existing_metadata(self):
        """Print non-empty non-binary metadata for {self.metadata.filename}."""
        metadata = self._filter_existing_metadata()
        self._display_metadata(metadata)

    def show_missing_metadata(self):
        """Print missing metadata for {self.metadata.filename}."""
        metadata = self._filter_missing_metadata()
        self._display_metadata(metadata)

    def _display_metadata(self, metadata):
        """Display metadata in a consistent format."""
        for key, value in metadata.items():
            if key == self.ART_METADATA:
                self._display_art(key, value)
            elif key == self.IMAGES_METADATA:
                self._display_images(key, value)
            elif key == self.LYRICS_METADATA:
                self._display_lyrics(key)
            elif value is None:
                print(f"{key}: <MISSING>")
            else:
                print(f"{key}: {value}")

    def _display_art(self, key, value):
        try:
            print(key + ": ")
            imgcat(value, width=24, height=24)
        except Exception as e:
            print(f"An error occurred while displaying art: {str(e)}")

    def _display_images(self, key, images):
        try:
            print(key + ": ")
            for image in images:
                imgcat(image.data, width=24, height=24)
                print()
        except Exception as e:
            print(f"An error occurred while displaying images: {str(e)}")

    def _display_lyrics(self, key):
        print(f"{key}: <LYRICS>")

    # Metadata Filtering Methods
    def _filter_existing_metadata(self):
        """Filter non-empty."""
        return {
            key: value
            for key, value in self.as_dict().items() if value
        }

    def _filter_missing_metadata(self):
        """Filter missing metadata."""
        return {
            key: None
            for key, value in self.as_dict().items() if not value
        }

    # Metadata Modification Methods
    def has_changed(self, new_meta, old_meta) -> bool:
        """Return True if there are changes to the metadata ignoring 'images'
        """
        # Excluding "images" as obj address always changes on update
        changed = any(
            key != "images" and key in old_meta and old_meta[key] != value
            for key, value in new_meta.items())
        return changed

    def batch_update_metadata(self, updates):
        """Updates """
        if isinstance(updates, dict):
            self.metadata.update(updates)
        else:
            for update in updates:
                key, value = update.split("=")
                try:
                    if hasattr(self.metadata, key):
                        setattr(self.metadata, key, value)
                    else:
                        possible_matches = get_close_matches(key,
                                                             dir(self.metadata),
                                                             n=5,
                                                             cutoff=0.6)
                        if possible_matches:
                            print(f"Invalid metadata field: {key}")
                            print(f"Did you mean? {', '.join(possible_matches)}")
                        else:
                            print(f"Invalid metadata field: {key}")
                except Exception as e:
                    print(f"An error occurred while updating metadata: {str(e)}")

    def single_update_metadata(self, field, value):
        try:
            if hasattr(self.metadata, field):
                setattr(self.metadata, field, value)
            else:
                possible_matches = get_close_matches(field,
                                                     dir(self.metadata),
                                                     n=5,
                                                     cutoff=0.6)
                if possible_matches:
                    print(f"Invalid metadata field: {field}")
                    print(f"Did you mean? {', '.join(possible_matches)}")
                else:
                    print(f"Invalid metadata field: {field}")
        except Exception as e:
            print(f"An error occurred while updating metadata: {str(e)}")

    def delete(self):
        """Delete metadata for {self.metadata.filename}."""
        try:
            self.metadata.delete()
        except Exception as e:
            print(f"An error occurred while deleting metadata: {str(e)}")

    def save(self):
        try:
            self.metadata.save()
        except Exception as e:
            print(f"An error occurred while saving metadata: {str(e)}")

    # Album Artwork Methods
    def resize_album_art(self, width, height):
        # Use the AlbumArtworkHandler class to resize album artwork
        pass

    def embed_album_art(self, image_path):
        # Use the AlbumArtworkHandler class to embed album artwork
        pass

    def export_album_art(self, output_path):
        # Use the AlbumArtworkHandler class to export album artwork
        pass
