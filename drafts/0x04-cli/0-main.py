from tags import TrackInfo
from data_store import DataStore
from query import Query

# Create an instance of TrackInfo
track_info = TrackInfo("../audio.mp3")

# Create an instance of DataStore
data_store = DataStore()


# Create an instance of Query
query = Query(track_info, data_store)

# Test fetching MusicBrainz data
print("Fetching MusicBrainz data...")
musicbrainz_data = query.fetch_musicbrainz_data()

if musicbrainz_data:
    print("Fetched MusicBrainz data:")
    print(musicbrainz_data)

# Test fetching DataStore data
print("\nFetching DataStore data...")
data_store_data = query.fetch_DataStore_data("musicbrainz")

if data_store_data:
    print("Fetched DataStore data:")
    print(data_store_data)
