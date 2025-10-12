import os

import musicbrainzngs  # type: ignore
import requests
import spotipy
from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyClientCredentials

load_dotenv()
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")

# Global cached Spotify client for performance
_spotify_client = None

# Configure MusicBrainz
musicbrainzngs.set_useragent("MetadataEditor", "0.1", "contact@example.com")
musicbrainzngs.set_rate_limit(limit_or_interval=1.0)  # 1 request per second


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
    """
    Robustly search for track metadata using MusicBrainz and Spotify.

    Args:
        query: Search query string (filename or "artist - title" format)

    Returns:
        tuple: (name, artist, album, cover_url) or (None, None, None, None) if not found
    """
    # Try MusicBrainz first (free, no API key needed)
    result = _search_musicbrainz(query)
    if result:
        return result

    # Fallback to Spotify
    result = _search_spotify(query)
    if result:
        return result

    return None, None, None, None


def _search_musicbrainz(query):
    """
    Search MusicBrainz for track metadata.

    Args:
        query: Search query string

    Returns:
        tuple: (name, artist, album, cover_url) or None
    """
    cleaned_query = _clean_query(query)

    # Strategy 1: Clean query search
    try:
        result = musicbrainzngs.search_recordings(query=cleaned_query, limit=5)
        metadata = _extract_musicbrainz_metadata(result)
        if metadata:
            return metadata
    except Exception as e:
        print(f"MusicBrainz cleaned search failed: {e}")

    # Strategy 2: Artist - Title split
    try:
        if " - " in query:
            parts = query.split(" - ", 1)
            if len(parts) == 2:
                artist_query, title_query = parts
                result = musicbrainzngs.search_recordings(
                    artist=artist_query.strip(), recording=title_query.strip(), limit=5
                )
                metadata = _extract_musicbrainz_metadata(result)
                if metadata:
                    return metadata
    except Exception as e:
        print(f"MusicBrainz artist-title search failed: {e}")

    return None


def _extract_musicbrainz_metadata(result):
    """
    Extract metadata from MusicBrainz search result.

    Args:
        result: MusicBrainz search result dictionary

    Returns:
        tuple: (name, artist, album, cover_url) or None
    """
    if not result or "recording-list" not in result:
        return None

    recordings = result["recording-list"]
    if not recordings:
        return None

    # Get best match (first result)
    recording = recordings[0]

    name = recording.get("title")
    artist = None
    album = None
    cover_url = None

    # Extract artist
    if "artist-credit" in recording and recording["artist-credit"]:
        artist = recording["artist-credit"][0]["artist"]["name"]

    # Extract album
    if "release-list" in recording and recording["release-list"]:
        album = recording["release-list"][0].get("title")
        release_id = recording["release-list"][0].get("id")

        # Try to get cover art from Cover Art Archive
        if release_id:
            try:
                cover_url = (
                    f"https://coverartarchive.org/release/{release_id}/front-250"
                )
                # Verify cover exists
                response = requests.head(cover_url, timeout=2)
                if response.status_code != 200:
                    cover_url = None
            except Exception:
                cover_url = None

    # Only return if we have at least name and artist
    if name and artist:
        return name, artist, album, cover_url

    return None


def _search_spotify(query):
    """
    Search Spotify for track metadata (fallback).

    Args:
        query: Search query string

    Returns:
        tuple: (name, artist, album, cover_url) or None
    """
    try:
        sp = _get_spotify_client()
    except Exception as e:
        print(f"Spotify client initialization failed: {e}")
        return None

    # Strategy 1: Clean query (remove file extension, special chars, video tags)
    try:
        cleaned_query = _clean_query(query)
        result = _search_and_extract(sp, cleaned_query)
        if result:
            return result
    except Exception as e:
        print(f"Spotify cleaned search failed: {e}")

    # Strategy 2: Try splitting "Artist - Title" format
    try:
        if " - " in query:
            parts = query.split(" - ", 1)
            if len(parts) == 2:
                artist_query, title_query = parts
                # Search with artist and track fields
                result = _search_and_extract(
                    sp, f"artist:{artist_query.strip()} track:{title_query.strip()}"
                )
                if result:
                    return result
    except Exception as e:
        print(f"Spotify artist-title split search failed: {e}")

    # Strategy 3: Try first significant words only (in case of long filenames)
    try:
        words = _clean_query(query).split()[:5]  # First 5 words
        if len(words) > 1:
            short_query = " ".join(words)
            result = _search_and_extract(sp, short_query)
            if result:
                return result
    except Exception as e:
        print(f"Spotify short query search failed: {e}")

    return None


def _search_and_extract(sp, query, limit=5):
    """
    Execute search and extract metadata from best match.

    Args:
        sp: Spotify client
        query: Search query string
        limit: Number of results to fetch

    Returns:
        tuple: (name, artist, album, cover_url) or None if no results
    """
    search = sp.search(q=query, limit=limit, type="track")

    if not search or "tracks" not in search:
        return None

    items = search["tracks"]["items"]
    if not items or len(items) == 0:
        return None

    # Get best match (first result)
    meta = items[0]

    # Extract with safe fallbacks
    name = meta.get("name")
    album = meta.get("album", {}).get("name")

    # Get primary artist
    artists = meta.get("album", {}).get("artists", [])
    artist = artists[0].get("name") if artists else None

    # Get highest quality cover image
    images = meta.get("album", {}).get("images", [])
    cover = images[0].get("url") if images else None

    # Only return if we have at least name and artist
    if name and artist:
        return name, artist, album, cover

    return None


def _clean_query(query):
    """
    Clean search query by removing common noise.

    Args:
        query: Original query string

    Returns:
        str: Cleaned query
    """
    import re

    # Remove file extension
    query = re.sub(r"\.(mp3|m4a|flac|wav|ogg|aac)$", "", query, flags=re.IGNORECASE)

    # Remove common video/audio tags
    patterns = [
        r"\(official\s*(video|audio|lyric|music\s*video)?\)",
        r"\[official\s*(video|audio|lyric|music\s*video)?\]",
        r"\(video\s*oficial\)",
        r"\[video\s*oficial\]",
        r"\(audio\s*oficial\)",
        r"\[audio\s*oficial\]",
        r"\(lyric\s*video\)",
        r"\[lyric\s*video\]",
        r"ft\.?\s+",
        r"feat\.?\s+",
        r"featuring\s+",
        r"\s*//\s*",
        r"\s*⧸⧸\s*",
    ]

    for pattern in patterns:
        query = re.sub(pattern, " ", query, flags=re.IGNORECASE)

    # Remove extra whitespace
    query = re.sub(r"\s+", " ", query).strip()

    return query
