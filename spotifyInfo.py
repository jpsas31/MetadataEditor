import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import json
 

def get_Track_Features(query):
    """
    Searches the query with the spotify api and returns info form the response
    """
    CLIENT_ID = "b14d9be57f1e47798431d7f16dfa6c66"
    CLIENT_SECRET = "fd9582b088b2445b8efcf83111dc72bd"
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
    # release_date = meta['album']['release_date']
    # length = meta['duration_ms']
    # popularity = meta['popularity']
    with open('data2.json', 'a') as outfile:
        json.dump([name,artist,album],outfile)
    return name,artist,album,cover
