from external_srs import MusicBrainAPI, DataStore, SpotifyAPI
from load_config import load_config

# Load the configuration data
config = load_config()

# Create instances of the MusicBrainAPI and SpotifyAPI classes
mb_api = MusicBrainAPI(app_name=config["MusicBrainAPI"]["app_name"],
                       app_version=config["MusicBrainAPI"]["app_version"],
                       app_contact=config["MusicBrainAPI"]["app_contact"])
sp_api = SpotifyAPI(client_id=config["SpotifyAPI"]["client_id"],
                    client_secret=config["SpotifyAPI"]["client_secret"])

# Search for "The Beatles" using both APIs
mb_result = mb_api.search_artist("The Beatles")
sp_result = sp_api.search_artist("The Beatles")

# Print the results from both sources
print("MusicBrainzNGs result:")
print(mb_result)
print("\nSpotify result:")
print(sp_result)

# Create an instance of the DataStore class
ds = DataStore()

# Store the results in the DataStore
ds.add_metadata("MusicBrainzNGs", mb_result)
ds.add_metadata("Spotify", sp_result)

# Retrieve and print the results from the DataStore
print("DataStore result:")
print("MusicBrainzNGs:", ds.get_metadata("MusicBrainzNGs"))
print("Spotify:", ds.get_metadata("Spotify"))
