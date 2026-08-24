#!/usr/bin/python3
import json
import yaml
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

lz_uri = 'spotify:artist:36QJpDe2go2KgaRleHCDTp'

spotify = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials())
results = spotify.artist_top_tracks(lz_uri)

for track in results['tracks'][:10]:
    print('track    : ' + track['name'])
    print('audio    : ' + track['preview_url'])
    print('cover art: ' + track['album']['images'][0]['url'])
    print()


file_name = 'results.json'
file_name_2 = 'results.yaml'

try:
    with open(file_name, 'w', encoding='utf-8')as f:
        json.dump(results, f, indent=4)
except Exception as e:
    print(f'JSON dump failed :{e}')

try:
    with open(file_name_2, 'w', encoding='utf-8')as f:
        yaml.dump(results, f, indent=4)
except Exception as e:
    print(f'YAMl dump failed :{e}')

