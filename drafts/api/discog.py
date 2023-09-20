#!/usr/bin/python3

import json
import yaml
import discogs_client

# Initialize the Discogs client
d = discogs_client.Client(
    'PataNgoma', user_token='prBSVqpdTzvXiBxTLXNjpCvjwIpvgqGcleCcTybo')

# Search for releases matching the query
results = d.search('Live And Die In Afrika',
                   type='release',
                   artist='sauti sol')

# Create a list to store release data dictionaries
release_data = []

# Extract and process relevant data from the search results
for release in results:
    release_dict = {
        'title': release.title,
        'artist': release.artists[0].name if release.artists else None,
        'year': release.year,
        'country': release.country,
        'format': release.formats[0]['name'] if release.formats else None
    }
    release_data.append(release_dict)

# Define file name
file_name = 'discog.json'
file_name_2 = 'discog.yaml'

try:
    # Save the list of release data dictionaries as JSON
    with open(file_name, 'w', encoding='utf-8') as f:
        json.dump(release_data, f, indent=4)
    print('Data saved to', file_name)
except Exception as e:
    print('Error in dumping:', e)

try:
    # Save the list of release data dictionaries as JSON
    with open(file_name_2, 'w', encoding='utf-8') as f:
        yaml.dump(release_data, f, indent=4)
    print('Data saved to', file_name_2)
except Exception as e:
    print('Error in dumping:', e)
