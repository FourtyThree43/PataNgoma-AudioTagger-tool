from metadata import TrackInfo, AlbumInfo
from db import Database

db_name = "tuto.db"

# Create a TrackInfo object
track_info = TrackInfo("05.track.mp3")
print(track_info.title)
print(track_info.album)
print(track_info.artist)
print(track_info.duration)


# Create an AlbumInfo object
album_info = AlbumInfo("Album Name", "Artist Name")
album_info.album_name = "Test01"
album_info.artist_name = "Test01"

print(album_info.album_name)
print(album_info.artist_name)
 
# # Add the track info to the album
album_info.add_track(track_info)
print(track_info.title)
print(track_info.album)
print(track_info.artist)
print(track_info.duration)

# Use the Database class as a context manager
with Database(db_name) as db:
    db.insert_album(album_info)
