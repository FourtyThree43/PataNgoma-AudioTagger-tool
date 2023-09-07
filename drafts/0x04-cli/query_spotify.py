# import os
import click
import spotipy
import yaml
from functools import lru_cache
from spotipy.oauth2 import SpotifyClientCredentials
from mediafile import MediaFile


def store(result):
    with open("store.yaml", "w") as f:
        yaml.safe_dump(result, f)


@lru_cache(maxsize=128)
def spotify_search(title, artist):
    print("Searching for", title, "by", artist)
    sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials())
    sp.auth = sp.auth_manager.get_access_token(as_dict=False)
    q = f"remaster track:{title} artist:{artist}".replace(" ", "%20")
    result = sp.search(q)
    if result["tracks"]["total"] == 0:
        print("No results found")
        exit(1)
    return result["tracks"]["items"], [{
        "name":
        result["tracks"]["items"][i]["name"],
        "artists":
        [j["name"] for j in result["tracks"]["items"][i]["artists"]],
        "popularity":
        result["tracks"]["items"][i]["popularity"],
    } for i in range(10)]


def get_search_params():
    file = click.prompt("Enter the path to the file",
                        type=click.Path(exists=True))
    try:
        media_file = MediaFile(file)
    except Exception as e:
        print("Error:", e)
        exit(1)
    if media_file.title and media_file.artist:
        artist = media_file.artist
        title = media_file.title
    else:
        print("Artist or title missing")
        artist = click.prompt("Enter the artist")
        title = click.prompt("Enter the title")
    return title, artist


def main():
    """Entry point for the application script"""
    title, artist = get_search_params()
    result, parsed_result = spotify_search(title, artist)
    for i in range(len(parsed_result)):
        print(
              f"{i+1}. {parsed_result[i]['name']}" +
              f" by {', '.join(parsed_result[i]['artists'])}" +
              f" (popularity: {parsed_result[i]['popularity']})")


if __name__ == "__main__":
    main()
