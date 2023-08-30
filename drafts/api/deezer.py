import deezer

from deezer.client import Client


# client = Client(app_id='629644',
#                        app_secret='8a21f8992a12c7414909728887216a1c)')

client = deezer.Client()

res = client.search('Sauti Sol')

print(res)
