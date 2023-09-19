#!/usr/bin/python3

import json
import yaml
from discogs_client import Client

pg = Client('PataNgoma', user_token='prBSVqpdTzvXiBxTLXNjpCvjwIpvgqGcleCcTybo')

st = pg.search('star song', type='release')
obj_dict = st.__dict__

new_obj = {}
for k, v in obj_dict.items():
    if not isinstance(v, str) and str(v).startswith('<') and str(v).endswith('>'):
        new_obj[k] = str(v)
    else:
        new_obj[k] = v
    print(new_obj)

file_name = 'discog2.json'
file_name2 = 'discog2.yaml'

try:
    with open(file_name, 'w', encoding='utf-8') as f:
        json.dump(new_obj, f, indent=4)
    print('Data saved to', file_name)
except Exception as e:
    print('Error in dumping:', e)

try:
    with open(file_name2, 'w', encoding='utf-8') as f:
        yaml.dump(new_obj, f, indent=4)
    print('Data saved to', file_name)
except Exception as e:
    print('Error in dumping:', e)
