from mediafile import MediaFile

f = MediaFile("05.track.mp3")

track_metadata = f.as_dict()

print("Track Metadata:")
ignored_keys = ['art', 'lyrics', 'genre']
for key, value in track_metadata.items():
    if key not in ignored_keys and value is not None:
        print(f"{key}: {value}")

print('\n')


f.update({'title': 'New', 'artist': 'New', 'genre': 'R&B'})
f.save()

print("------------------------")
print('\n')
print("Modifided Track Metadata:")
ignored_keys = ['art', 'lyrics', 'genre']
for key, value in track_metadata.items():
    if key not in ignored_keys:
        print(f"{key}: {value}")

print()
