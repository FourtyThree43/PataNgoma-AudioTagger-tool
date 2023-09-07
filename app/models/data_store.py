import json
import os
import threading
import logging


class DataStore:

    def __init__(self, file_path="datastore.json"):
        self.metadata = {}
        self.file_path = file_path
        self.lock = threading.Lock()
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

    def add_metadata(self, source: str, data: dict):
        """Add metadata from an external source to the datastore."""
        with self.lock:
            try:
                if source not in self.metadata:
                    self.metadata[source] = []
                self.metadata[source].append(data)
                self._save_metadata()
            except Exception as e:
                self.logger.error(f"Error adding metadata: {str(e)}")

    def get_metadata(self, source: str):
        """Get metadata from a specific external source."""
        with self.lock:
            try:
                self._load_metadata()
                return self.metadata.get(source, [])
            except FileNotFoundError:
                return []
            except json.JSONDecodeError as e:
                self.logger.error(f"Error decoding JSON: {str(e)}")
                return []

    def get_all_metadata(self):
        """Get all metadata from all sources."""
        with self.lock:
            try:
                self._load_metadata()
                return self.metadata
            except FileNotFoundError:
                return {}
            except json.JSONDecodeError as e:
                self.logger.error(f"Error decoding JSON: {str(e)}")
                return {}

    def _load_metadata(self):
        """Load metadata from the JSON file."""
        if os.path.exists(self.file_path):
            with open(self.file_path, 'r') as f:
                self.metadata = json.load(f)

    def _save_metadata(self):
        """Save metadata to the JSON file."""
        with open(self.file_path, 'w') as f:
            json.dump(self.metadata, f, indent=4)
