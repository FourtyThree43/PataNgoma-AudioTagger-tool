import json
import yaml
from mediafile import MediaFile

f = MediaFile("music/track.mp3")

track_metadata = f.as_dict()
dump = {
    k: v
    for k, v in track_metadata.items() if k not in ("art", "images")
}
keys = track_metadata.keys()
dump.update({k: "<BINARY>" for k in ("art", "images") if k in keys})
# dump.update({k: "<TOO_LONG>" for k in ("lyrics") if "lyrics" in keys})

#   try:
#       with open("as_dict.json", "w") as j:
#           json.dump(dump, j, indent=4)
#   except Exception as e:
#       print(f"json_error: {e}")

try:
    with open("as_dict.yaml", "w") as y:
        yaml.dump(dump, y, indent=4, sort_keys=False)
except Exception as e:
    print(f"yaml_error: {e}")

#   print("Track Metadata:")
#   ignored_keys = ['art', 'lyrics', 'genre']
#   for key, value in track_metadata.items():
#       if key not in ignored_keys and value is not None:
#           print(f"{key}: {value}")

#   print('\n')

#   f.update({'title': 'New', 'artist': 'New', 'genre': 'R&B'})
#   f.save()

#   print("------------------------")
#   print('\n')
#   print("Modifided Track Metadata:")
#   ignored_keys = ['art', 'lyrics', 'genre']
#   for key, value in track_metadata.items():
#       if key not in ignored_keys:
#           print(f"{key}: {value}")

#   print()
