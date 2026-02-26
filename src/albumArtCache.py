from __future__ import annotations

import hashlib
import os
import pickle
from dataclasses import dataclass
from pathlib import Path

from src.logging_config import setup_logging

logger = setup_logging(__name__)


@dataclass
class CacheStats:
    """Statistics about the album art cache."""

    memory_items: int
    memory_max: int
    disk_items: int
    disk_size_bytes: int
    disk_size_mb: float


class AlbumArtCache:
    """Two-tier cache (memory + disk) for album art to avoid regenerating ASCII art."""

    def __init__(
        self,
        cache_dir: str | Path | None = None,
        max_memory_cache_size: int = 50,
    ):
        self._memory_cache: dict[str, str] = {}
        self._cache_access_order: list[str] = []
        self.max_memory_cache_size = max_memory_cache_size

        if cache_dir is None:
            cache_home = os.environ.get("XDG_CACHE_HOME", os.path.expanduser("~/.cache"))
            self.cache_dir = Path(cache_home) / "metadata_editor" / "album_art"
        else:
            self.cache_dir = Path(cache_dir)

        self.cache_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Album art cache directory: {self.cache_dir}")
        logger.info(f"Memory cache max size: {self.max_memory_cache_size}")

    def _get_cache_key(
        self,
        file_path: str,
        image_data: bytes,
        album_art_size: tuple[int, int],
    ) -> str:
        """Generate a unique cache key based on file path and image data hash."""

        image_hash = hashlib.md5(image_data).hexdigest()

        path_hash = hashlib.md5(file_path.encode()).hexdigest()
        return f"{path_hash}_{image_hash}_{album_art_size}.pkl"

    def _update_lru(self, cache_key: str) -> None:
        """Update LRU tracking for a cache key."""
        if cache_key in self._cache_access_order:
            self._cache_access_order.remove(cache_key)
        self._cache_access_order.append(cache_key)

        while len(self._memory_cache) > self.max_memory_cache_size:
            oldest_key = self._cache_access_order.pop(0)
            if oldest_key in self._memory_cache:
                del self._memory_cache[oldest_key]
                logger.debug(f"Evicted from memory cache: {oldest_key}")

    def get(
        self,
        file_path: str,
        image_data: bytes,
        album_art_size: tuple[int, int],
    ) -> str | None:
        """Get cached ASCII art for a file path and image data.
        Checks memory cache first, then disk cache."""
        try:
            cache_key = self._get_cache_key(file_path, image_data, album_art_size)

            if cache_key in self._memory_cache:
                logger.debug(f"Memory cache hit for: {file_path}")
                self._update_lru(cache_key)
                return self._memory_cache[cache_key]

            cache_file = self.cache_dir / cache_key
            if cache_file.exists():
                logger.debug(f"Disk cache hit for: {file_path}")
                with open(cache_file, "rb") as f:
                    ascii_art = pickle.load(f)

                self._memory_cache[cache_key] = ascii_art
                self._update_lru(cache_key)
                logger.debug(f"Promoted to memory cache (size: {len(self._memory_cache)})")

                return ascii_art
            else:
                logger.debug(f"Cache miss for: {file_path}")
                return None
        except Exception as e:
            logger.error(f"Error reading from cache: {e}")
            return None

    def set(
        self,
        file_path: str,
        image_data: bytes,
        ascii_art: str,
        album_art_size: tuple[int, int],
    ) -> None:
        """Cache ASCII art for a file path and image data.
        Stores in both memory and disk cache."""
        try:
            cache_key = self._get_cache_key(file_path, image_data, album_art_size)

            self._memory_cache[cache_key] = ascii_art
            self._update_lru(cache_key)
            logger.debug(f"Stored in memory cache (size: {len(self._memory_cache)})")

            cache_file = self.cache_dir / cache_key
            with open(cache_file, "wb") as f:
                pickle.dump(ascii_art, f)

            logger.debug(f"Stored in disk cache: {cache_file}")
        except Exception as e:
            logger.error(f"Error writing to cache: {e}")

    def clear(self, clear_disk: bool = True) -> None:
        """Clear cache.

        Args:
            clear_disk: If True, also clear disk cache. If False, only clear memory cache.
        """
        try:
            self._memory_cache.clear()
            self._cache_access_order.clear()
            logger.info("Memory cache cleared")

            if clear_disk:
                for cache_file in self.cache_dir.glob("*.pkl"):
                    cache_file.unlink()
                logger.info("Disk cache cleared")
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")

    def get_cache_size(self) -> int:
        """Get the total size of the disk cache in bytes."""
        try:
            total_size = sum(f.stat().st_size for f in self.cache_dir.glob("*.pkl"))
            return total_size
        except Exception as e:
            logger.error(f"Error calculating cache size: {e}")
            return 0

    def get_cache_stats(self) -> CacheStats:
        """Get statistics about the cache."""
        try:
            disk_files = list(self.cache_dir.glob("*.pkl"))
            disk_size = sum(f.stat().st_size for f in disk_files)

            return CacheStats(
                memory_items=len(self._memory_cache),
                memory_max=self.max_memory_cache_size,
                disk_items=len(disk_files),
                disk_size_bytes=disk_size,
                disk_size_mb=disk_size / (1024 * 1024),
            )
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return CacheStats(
                memory_items=0,
                memory_max=self.max_memory_cache_size,
                disk_items=0,
                disk_size_bytes=0,
                disk_size_mb=0.0,
            )
