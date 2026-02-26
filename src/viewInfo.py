from __future__ import annotations

import bisect
import os
from collections.abc import Mapping

from src.logging_config import setup_logging

logger = setup_logging(__name__)


class ViewInfo:
    def __init__(self, dir: str) -> None:
        self.dir = dir
        os.chdir(dir)
        self.canciones: list[str] = os.listdir(dir)
        self.canciones = [x for x in self.canciones if "mp3" in x]
        self.canciones.sort()
        self._metadata_cache: dict[str, tuple[str, str, str, str]] = {}

    def get_dir(self) -> str:
        return self.dir

    def add_song(self, song: str) -> None:
        bisect.insort(self.canciones, song)

    def delete_song(self, song: str) -> None:
        self.canciones.remove(song)

        if song in self._metadata_cache:
            del self._metadata_cache[song]

    def song_info(self, index: int) -> tuple[str, str, str, str]:
        if len(self.canciones) == 0:
            return ("", "", "", "No Cover")

        cancion = self.canciones[index]

        if cancion in self._metadata_cache:
            return self._metadata_cache[cancion]

        from src.tagModifier import MP3Editor

        metadata = MP3Editor(cancion).song_info()
        self._metadata_cache[cancion] = metadata
        return metadata

    def invalidate_cache(self, filename: str) -> None:
        """Invalidate cache when metadata is edited."""
        if filename in self._metadata_cache:
            del self._metadata_cache[filename]

    def song_file_name(self, index: int) -> str:
        if len(self.canciones) > 0:
            return self.canciones[index]
        return "None"

    def songs_len(self) -> int:
        return len(self.canciones)

    def is_song(self, filename: str) -> bool:
        return filename in self.canciones

    def get_current_song(self) -> str | None:
        """Get the full path of the current/first song."""
        if len(self.canciones) > 0:
            return f"{self.dir}/{self.canciones[0]}"
        return None

    def get_metadata_cache(self) -> Mapping[str, tuple[str, str, str, str]]:
        return self._metadata_cache.copy()
