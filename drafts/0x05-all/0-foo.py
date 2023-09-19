from tags import TrackInfo
from data_store import DataStore
from query import Query

track_info = TrackInfo("../music/track")
data_store = DataStore()
query = Query(track_info, data_store)

print("Fetching MusicBrainz data...")
musicbrainz_data = query.fetch_musicbrainz_data()

if musicbrainz_data:
    print("Fetched MusicBrainz data:")
    print(musicbrainz_data)

# print("\nFetching DataStore data...")
# data_store_data = query.fetch_DataStore_data("musicbrainz")

# if data_store_data:
#     print("Fetched DataStore data:")
#     print(data_store_data)
