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
        self._metadata_cache = {}

    def get_dir(self):
        return self.dir

    def add_song(self, song):
        bisect.insort(self.canciones, song)

    def delete_song(self, song):
        self.canciones.remove(song)

        if song in self._metadata_cache:
            del self._metadata_cache[song]

    def song_info(self, index):
        if len(self.canciones) == 0:
            return "", "", "", "No Cover"

        cancion = self.canciones[index]

        if cancion in self._metadata_cache:
            return self._metadata_cache[cancion]

        metadata = tagModifier.MP3Editor(cancion).song_info()
        self._metadata_cache[cancion] = metadata
        return metadata

    def invalidate_cache(self, filename):
        """Invalidate cache when metadata is edited."""
        if filename in self._metadata_cache:
            del self._metadata_cache[filename]

    def song_file_name(self, index):
        if len(self.canciones) > 0:
            return self.canciones[index]
        return "None"

    def songs_len(self):
        return len(self.canciones)

    def is_song(self, filename):
        return filename in self.canciones

    def get_current_song(self):
        """Get the full path of the current/first song."""
        if len(self.canciones) > 0:
            return f"{self.dir}/{self.canciones[0]}"
        return None
