import click
import os
import spotipy
import yaml
from InquirerPy import inquirer
from InquirerPy.validator import PathValidator
from dotenv import load_dotenv
from functools import lru_cache
from spotipy.oauth2 import SpotifyClientCredentials
from mediafile import MediaFile
from datetime import datetime
from rgbprint import gradient_print, gradient_scroll, Color


def storage():
    home = os.path.expanduser("~")
    storage_path = os.path.normpath(f"{home}/.patangoma_store/")
    if not os.path.exists(storage_path):
        os.makedirs(storage_path)
    return storage_path

storage_file = os.path.join(storage(), "sp_storage.yaml")


def store(dump: dict):
    """Save queries for future reference"""
    try:
        with open(storage_file, "r") as f:
            loaded = yaml.safe_load(f)
            loaded.update(dump)
        with open(storage_file, "w") as f:
            yaml.safe_dump(loaded, f)
    except FileNotFoundError:
        with open(storage_file, "w") as f:
            yaml.safe_dump(dump, f)


def cached():
    """Retrieve cached queries from the store"""
    try:
        with open(storage_file, "r") as f:
            cache: dict = yaml.safe_load(f)
    except FileNotFoundError:
        cache = {}
    return cache


def get_search_params() -> tuple:
    """Obtain query parameters (`artist` and `track title`) from file or user"""
    path = inquirer.filepath(message="Enter file name:",
                             only_files=True,
                             validate=PathValidator(is_file=True,
                                                    message="Invalid path"),
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


@lru_cache(maxsize=128)
def spotify_search(title: str, artist: str) -> tuple:
    """Search for matching tracks in the Spotify database using track title and artist name"""
    # end_color = Color.random
    gradient_print(f"\nSearching for {title} by {artist}...\n",
                    start_color=Color.gold,
                    end_color=0xFF00FF)
    load_dotenv()
    sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials())
    q = f"remaster track:{title} artist:{artist}".replace(" ", "%20")
    cache = cached()
    if q in cache:
        result: dict = cache[q]
    else:
        result: dict = sp.search(q)  # pyright: ignore
        if result["tracks"]["total"] == 0:
            click.secho("No matches found!", fg="yellow")
            return [], []
        else:
            store({q: result})
    return result.get("tracks", {}).get("items", []), [{
        "name":
        result.get("tracks", {}).get("items", [])[i].get("name", ""),
        "artists": [
            j.get("name", "") for j in result.get("tracks", {}).get(
                "items", [])[i].get("artists", [])
        ],
        "popularity":
        result.get("tracks", {}).get("items", [])[i].get("popularity", 0),
    } for i in range(10)]


def get_updates(result: list, parsed_result: list):
    """Return a dictionary of tags from matching information returned by the `spotify_search` function"""
    if not (result and parsed_result):
        return {}
    selection: str = inquirer.select(
        message="Found matches, please select a track:",
        choices=[
            f"{i+1}. {parsed_result[i]['name']}" +
            f" by {', '.join(parsed_result[i]['artists'])}" +
            f" (popularity: {parsed_result[i]['popularity']})"
            for i in range(len(parsed_result))
        ],
        qmark=">",
        amark="✔️").execute()
    selected = int(selection.split(".")[0])
    raw: dict = result[selected - 1]
    update = {}
    update["title"] = raw["name"]
    update["album"] = raw["album"]["name"]
    update["artists"] = [i["name"] for i in raw["artists"]]
    update["artist"] = update["artists"][0]
    update["date"] = datetime.fromisoformat(raw["album"]["release_date"])
    return update
