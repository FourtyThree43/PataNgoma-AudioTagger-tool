from datetime import datetime
from dotenv import load_dotenv
from functools import lru_cache
from InquirerPy import inquirer
from InquirerPy.validator import PathValidator
from mediafile import MediaFile
from spotipy.oauth2 import SpotifyClientCredentials
import click
import spotipy
import yaml


class SpotifyAPI:

    def __init__(self):
        self.load_dotenv()
        self.sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials())

    @staticmethod
    def load_dotenv():
        load_dotenv()

    @staticmethod
    def store(dump: dict):
        try:
            with open("store.yaml", "r") as f:
                loaded = yaml.safe_load(f)
                loaded.update(dump)
            with open("store.yaml", "w") as f:
                yaml.safe_dump(loaded, f)
        except FileNotFoundError:
            with open("store.yaml", "w") as f:
                yaml.safe_dump(dump, f)

    @staticmethod
    def update_media_file(media_file: MediaFile, result: list,
                          parsed_result: list):
        selection: str = inquirer.select(
            message="Select a track:",
            choices=[
                f"{i+1}. {parsed_result[i]['name']}" +
                f" by {', '.join(parsed_result[i]['artists'])}" +
                f" (popularity: {parsed_result[i]['popularity']})"
                for i in range(len(parsed_result))
            ],
            amark="✔").execute()
        selected = int(selection.split(".")[0])
        raw: dict = result[selected - 1]
        update = {}
        update["title"] = raw["name"]
        update["album"] = raw["album"]["name"]
        update["artists"] = [i["name"] for i in raw["artists"]]
        update["artist"] = update["artists"][0]
        update["length"] = raw["duration_ms"] / 1000
        update["date"] = datetime.fromisoformat(raw["album"]["release_date"])
        media_file.update(update)
        media_file.save()
        print("Updated file:", media_file.path)

    @staticmethod
    def spotify_search(title: str, artist: str) -> tuple:
        print("Searching for", title, "by", artist)
        q = f"remaster track:{title} artist:{artist}".replace(" ", "%20")
        try:
            with open("store.yaml", "r") as f:
                cached: dict = yaml.safe_load(f)
        except FileNotFoundError:
            cached = {}
        if q in cached:
            result: dict = cached[q]
        else:
            result: dict = self.sp.search(q)  # pyright: ignore
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

    @staticmethod
    def get_search_params() -> tuple:
        path = inquirer.filepath(message="Enter file name:",
                                 only_files=True,
                                 validate=PathValidator(
                                     is_file=True, message="Invalid path"),
                                 amark="✔").execute()
        try:
            media_file = MediaFile(path)
        except Exception as e:
            print("Error:", e)
            exit(1)
        if media_file.title and media_file.artist:
            artist = media_file.artist
            title = media_file.title
        else:
            click.echo("Artist or title missing")
            artist = inquirer.text(message="Enter the artist:").execute()
            title = inquirer.text(message="Enter the title:").execute()
        return media_file, title, artist


if __name__ == "__main__":
    spotify_api = SpotifyAPI()
    media_file, title, artist = spotify_api.get_search_params()
    result, parsed_result = spotify_api.spotify_search(title, artist)
    spotify_api.update_media_file(media_file, result, parsed_result)
