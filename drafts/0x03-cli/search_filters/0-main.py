from external_sorces import MusicBrainAPI, DataStore
from query import Query

# Create an instance of the MusicBrainAPI class
mb_api = MusicBrainAPI(app_name="MyApp",
                       app_version="1.0",
                       app_contact="myemail@example.com")

# Search for an artist using the MusicBrainAPI class
artist_result = mb_api.search_artist("Rick Astley")

# Create an instance of the DataStore class
datastore = DataStore()

# Add the search result to the datastore
datastore.add_metadata(source="MusicBrainzNGs", data=artist_result)

# Get the metadata from the datastore
metadata = datastore.get_metadata(source="MusicBrainzNGs")

# Process the metadata as needed
# for artist in metadata[0]['artist-list']:
#     print(f"Artist: {artist['name']}")
query = Query(datastore)
results = query.search('id', 'db92a151-1ac2-438b-bc43-b82e149ddd50')
print(results)
