import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import json
import os
from dotenv import load_dotenv

load_dotenv()
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')

def get_Track_Features(query): 
    client_credentials_manager =SpotifyClientCredentials(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET)
    sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
    search=sp.search(query)

    if (len(search["tracks"]["items"])==0): 
        return None,None,None,None

    meta=search["tracks"]["items"][0]
    name = meta['name']
    album = meta['album']['name']
    artist = meta['album']['artists'][0]['name']
    cover=meta['album']['images'][0]['url']
   
    return name,artist,album,cover
