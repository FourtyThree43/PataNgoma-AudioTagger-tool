# mediafile.py
from mediafile import MediaFile


class MetaData:

    def __init__(self, file_path):
        self.file = file_path
        self.metadata = MediaFile(file_path)

    def as_dict(self):
        return dict(self.metadata.as_dict())

    def show_metadata(self):
        print(f"Metadata of {self.file}:")
        for key, value in self.as_dict().items():
            print(f"{key}: {value}")

    def update_metadata(self, updates):
        # for update in updates:
        #     key, value = update.split("=")
        #     self.metadata[key] = value
        pass

    def save(self):
        self.metadata.save()
