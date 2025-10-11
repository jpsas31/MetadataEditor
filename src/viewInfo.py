import bisect
import os

import src.tagModifier as tagModifier


class ViewInfo:
    def __init__(self, dir):
        self.dir = dir
        tagModifier.dir = dir
        os.chdir(dir)
        self.canciones = os.listdir(dir)
        self.canciones = [x for x in self.canciones if "mp3" in x]
        self.canciones.sort()
        self._metadata_cache = {}  # Cache: {filename: (title, album, artist, album_art)}

    def getDir(self):
        return self.dir

    def addSong(self, song):
        # Use bisect for O(n) insertion instead of O(n log n) sort
        bisect.insort(self.canciones, song)

    def deleteSong(self, song):
        # No sort needed - list remains sorted after removal
        self.canciones.remove(song)
        # Invalidate cache for removed song
        if song in self._metadata_cache:
            del self._metadata_cache[song]

    def songInfo(self, index):
        if len(self.canciones) == 0:
            return "", "", "", "No Cover"

        cancion = self.canciones[index]

        # Check cache first for massive performance improvement
        if cancion in self._metadata_cache:
            return self._metadata_cache[cancion]

        # Load metadata and cache it
        metadata = tagModifier.MP3Editor(cancion).song_info()
        self._metadata_cache[cancion] = metadata
        return metadata

    def invalidate_cache(self, filename):
        """Invalidate cache when metadata is edited."""
        if filename in self._metadata_cache:
            del self._metadata_cache[filename]

    def songFileName(self, index):
        if len(self.canciones) > 0:
            return self.canciones[index]
        return "None"

    def songsLen(self):
        return len(self.canciones)

    def isSong(self, filename):
        return filename in self.canciones

    def getCurrentSong(self):
        """Get the full path of the current/first song."""
        if len(self.canciones) > 0:
            return f"{self.dir}/{self.canciones[0]}"
        return None
