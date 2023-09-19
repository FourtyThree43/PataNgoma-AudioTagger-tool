import json
import logging
import os
import threading
import yaml
from sp import storage

storage_file = os.path.join(storage(), "mb_storage.yaml")


class DataStore:
    """A simple datastore for storing metadata from external sources."""

    def __init__(self, file_path=storage_file, fmt='yaml'):
        self.metadata = {}
        self.file_path = file_path
        self.fmt = fmt
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
            except (json.JSONDecodeError, yaml.YAMLError) as e:
                self.logger.error(f"Error decoding {self.fmt.upper()}: {str(e)}")
                return []

    def get_all_metadata(self):
        """Get all metadata from all sources."""
        with self.lock:
            try:
                self._load_metadata()
                return self.metadata
            except FileNotFoundError:
                return {}
            except (json.JSONDecodeError, yaml.YAMLError) as e:
                self.logger.error(f"Error decoding {self.fmt.upper()}: {str(e)}")
                return {}

    def _load_metadata(self):
        """Load metadata from the file."""
        if os.path.exists(self.file_path):
            with open(self.file_path, 'r') as f:
                if self.fmt == 'json':
                    self.metadata = json.load(f)
                else:  # default is yaml
                    self.metadata = yaml.safe_load(f)

    def _save_metadata(self):
        """Save metadata to the file."""
        with open(self.file_path, 'w') as f:
            if self.fmt == 'json':
                json.dump(self.metadata, f, indent=4)
            else:  # default is yaml
                yaml.safe_dump(self.metadata, f)
