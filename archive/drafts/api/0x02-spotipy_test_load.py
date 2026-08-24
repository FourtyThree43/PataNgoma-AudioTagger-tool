"""Module to load and display images from the web.
"""

from imgcat import imgcat as img
from requests import request as req
import json
import yaml

with open("results.yaml", "r") as f:
    results_01 = yaml.safe_load(f)


"""
<class 'dict'>
dict_keys(['tracks'])
dict_keys(['tracks'])
dict_keys([
    'album', 'artists', 'disc_number', 'duration_ms', 'explicit',
    'external_ids', 'external_urls', 'href', 'id', 'is_local', 'is_playable',
    'name', 'popularity', 'preview_url', 'track_number', 'type', 'uri'
])
dict_keys([
    'album_type', 'artists', 'external_urls', 'href', 'id', 'images',
    'is_playable', 'name', 'release_date', 'release_date_precision',
    'total_tracks', 'type', 'uri'
])
dict_keys(['height', 'url', 'width'])
"""

# print(type(results_01))
# print(results_01.keys())
# print(results_01['tracks'][0].keys())
# print(results_01['tracks'][0]['album'].keys())
# print(results_01['tracks'][0]['album']['images'][0].keys())
# print(results_01['tracks'][0]['album']['images'][0]['url'])

for key, value in results_01['tracks'][0]['album'].items():
    print(f"{key}: ", end="\n")
    if key == "images":
        for image in value:
            print(f"    {image['url']}")
            artwork = req("GET", image['url']).content
            img(artwork)

    elif key == "artists":
        for artist in value:
            print(f"    {artist['name']}")
    else:
        print(f"    {value}")

