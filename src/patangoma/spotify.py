import click
import spotipy
import yaml
from InquirerPy import inquirer
from InquirerPy.validator import PathValidator
from dotenv import load_dotenv
from functools import lru_cache
from spotipy.oauth2 import SpotifyClientCredentials
from mediafile import MediaFile
from datetime import datetime


class SpotifyAPI:
    """Encapsulates methods for interacting with the Spotify API"""

    def __init__(self, mediafile_object: MediaFile, artist: str, title: str):
        """Class constructor"""
        self.mediafile_object = mediafile_object
        self.artist = artist
        self.title = title

    def search(self, title: str, artist: str):
        """Look up a track in the Spotify database based on track title and artist"""
        load_dotenv()
        sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials())
        # sp.auth = sp.auth_manager.get_access_token(as_dict=False)
        q = f"remaster track:{self.title} artist:{self.artist}".replace(" ", "%20")
        cached = self.cache()
        if q in cached:
            result: dict = cached[q]
        else:
            result: dict = sp.search(q)  # pyright: ignore
            if result["tracks"]["total"] == 0:
                print("Search failed, exiting")
                exit(1)
            self.store({q: result})
        return result["tracks"]["items"], [{
        "name":
        result["tracks"]["items"][i]["name"],
        "artists":
        [j["name"] for j in result["tracks"]["items"][i]["artists"]],
        "popularity":
        result["tracks"]["items"][i]["popularity"],
    } for i in range(10)]


    
    def cache(self):
        try:
            with open("store.yaml", "r") as f:
                cached: dict = yaml.safe_load(f)
        except FileNotFoundError:
            cached = {}
        return cached

    def store(self, dump: dict):
        try:
            with open("store.yaml", "r") as f:
                loaded = yaml.safe_load(f)
                loaded.update(dump)
            with open("store.yaml", "w") as f:
                yaml.safe_dump(loaded, f)
        except FileNotFoundError:
            with open("store.yaml", "w") as f:
                yaml.safe_dump(dump, f)
