import os

import spotipy
from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyClientCredentials

load_dotenv()
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")

# Global cached Spotify client for performance
_spotify_client = None


def _get_spotify_client():
    """Get or create cached Spotify client to avoid re-authentication."""
    global _spotify_client
    if _spotify_client is None:
        client_credentials_manager = SpotifyClientCredentials(
            client_id=CLIENT_ID, client_secret=CLIENT_SECRET
        )
        _spotify_client = spotipy.Spotify(
            client_credentials_manager=client_credentials_manager
        )
    return _spotify_client


def get_Track_Features(query):
    sp = _get_spotify_client()  # Reuse cached client
    search = sp.search(query)

    if len(search["tracks"]["items"]) == 0:
        return None, None, None, None

    meta = search["tracks"]["items"][0]
    name = meta["name"]
    album = meta["album"]["name"]
    artist = meta["album"]["artists"][0]["name"]
    cover = meta["album"]["images"][0]["url"]

    return name, artist, album, cover
