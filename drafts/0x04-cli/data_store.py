import json


class DataStore:

    def __init__(self):
        self.metadata = {}

    def add_metadata(self, source: str, data: dict):
        """Add metadata from an external source to the datastore."""
        if source not in self.metadata:
            self.metadata[source] = []
        self.metadata[source].append(data)
        with open('datastore.json', 'w') as f:
            json.dump(self.metadata, f, indent=4)

    def get_metadata(self, source: str):
        """Get metadata from a specific external source."""
        with open('datastore.json', 'r') as f:
            self.metadata = json.load(f)
        return self.metadata.get(source, [])

    def get_all_metadata(self):
        """Get all metadata from all sources."""
        with open('datastore.json', 'r') as f:
            self.metadata = json.load(f)
        return self.metadata
