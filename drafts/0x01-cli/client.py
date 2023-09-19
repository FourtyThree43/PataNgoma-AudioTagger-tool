#!env/bin/python

import json
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

urn = 'spotify:artist:3jOstUTkEu2JkjvRdBA5Gu'
sp = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials())

artist = sp.artist(urn)
print(json.dumps(artist, indent=4))
print("_"*132 + "\n")
user = sp.user('plamere')
print(json.dumps(user, indent=4))
