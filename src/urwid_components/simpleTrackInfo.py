import hashlib
import logging
import os
import pickle
from io import BytesIO
from pathlib import Path

import urwid
from climage import convert_pil
from mutagen.id3 import ID3
from PIL import Image, ImageFile

from src.singleton import BorgSingleton
from src.urwid_components.ansiWidget import ANSIWidget

logging.basicConfig(
    filename="/tmp/album_art_debug.log",
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filemode="w",
)
logger = logging.getLogger(__name__)

state = BorgSingleton()


class AlbumArtCache:
    """Two-tier cache (memory + disk) for album art to avoid regenerating ASCII art."""

    def __init__(self, cache_dir=None, max_memory_cache_size=50):
        self._memory_cache = {}
        self._cache_access_order = []
        self.max_memory_cache_size = max_memory_cache_size

        if cache_dir is None:
            cache_home = os.environ.get(
                "XDG_CACHE_HOME", os.path.expanduser("~/.cache")
            )
            self.cache_dir = Path(cache_home) / "metadata_editor" / "album_art"
        else:
            self.cache_dir = Path(cache_dir)

        self.cache_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Album art cache directory: {self.cache_dir}")
        logger.info(f"Memory cache max size: {self.max_memory_cache_size}")

    def _get_cache_key(self, file_path, image_data):
        """Generate a unique cache key based on file path and image data hash."""

        image_hash = hashlib.md5(image_data).hexdigest()

        path_hash = hashlib.md5(file_path.encode()).hexdigest()
        return f"{path_hash}_{image_hash}.pkl"

    def _update_lru(self, cache_key):
        """Update LRU tracking for a cache key."""
        if cache_key in self._cache_access_order:
            self._cache_access_order.remove(cache_key)
        self._cache_access_order.append(cache_key)

        while len(self._memory_cache) > self.max_memory_cache_size:
            oldest_key = self._cache_access_order.pop(0)
            if oldest_key in self._memory_cache:
                del self._memory_cache[oldest_key]
                logger.debug(f"Evicted from memory cache: {oldest_key}")

    def get(self, file_path, image_data):
        """Get cached ASCII art for a file path and image data.
        Checks memory cache first, then disk cache."""
        try:
            cache_key = self._get_cache_key(file_path, image_data)

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
                logger.debug(
                    f"Promoted to memory cache (size: {len(self._memory_cache)})"
                )

                return ascii_art
            else:
                logger.debug(f"Cache miss for: {file_path}")
                return None
        except Exception as e:
            logger.error(f"Error reading from cache: {e}")
            return None

    def set(self, file_path, image_data, ascii_art):
        """Cache ASCII art for a file path and image data.
        Stores in both memory and disk cache."""
        try:
            cache_key = self._get_cache_key(file_path, image_data)

            self._memory_cache[cache_key] = ascii_art
            self._update_lru(cache_key)
            logger.debug(f"Stored in memory cache (size: {len(self._memory_cache)})")

            cache_file = self.cache_dir / cache_key
            with open(cache_file, "wb") as f:
                pickle.dump(ascii_art, f)

            logger.debug(f"Stored in disk cache: {cache_file}")
        except Exception as e:
            logger.error(f"Error writing to cache: {e}")

    def clear(self, clear_disk=True):
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

    def get_cache_size(self):
        """Get the total size of the disk cache in bytes."""
        try:
            total_size = sum(f.stat().st_size for f in self.cache_dir.glob("*.pkl"))
            return total_size
        except Exception as e:
            logger.error(f"Error calculating cache size: {e}")
            return 0

    def get_cache_stats(self):
        """Get statistics about the cache."""
        try:
            disk_files = list(self.cache_dir.glob("*.pkl"))
            disk_size = sum(f.stat().st_size for f in disk_files)

            return {
                "memory_items": len(self._memory_cache),
                "memory_max": self.max_memory_cache_size,
                "disk_items": len(disk_files),
                "disk_size_bytes": disk_size,
                "disk_size_mb": disk_size / (1024 * 1024),
            }
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {}


_album_art_cache = AlbumArtCache()


class SimpleTrackInfo(urwid.Pile):
    """Simple component with album art on top and track info below."""

    def __init__(self):
        logger.info("SimpleTrackInfo.__init__ called")

        self.album_art_container = urwid.Text(
            "♪\n\nNo Album Art\nAvailable", align="center"
        )

        self.filename_text = urwid.Text("", align="center")
        self.title_text = urwid.Text("", align="center")
        self.album_text = urwid.Text("", align="center")
        self.artist_text = urwid.Text("", align="center")

        metadata_pile = urwid.Pile(
            [
                urwid.AttrMap(self.filename_text, "Title"),
                urwid.Text("Title", align="center"),
                urwid.AttrMap(self.title_text, "Title"),
                urwid.Text("Album", align="center"),
                urwid.AttrMap(self.album_text, "Title"),
                urwid.Text("Artist", align="center"),
                urwid.AttrMap(self.artist_text, "Title"),
            ]
        )

        super().__init__(
            [
                (
                    "weight",
                    4,
                    urwid.Filler(
                        self.album_art_container,
                        valign="middle",
                    ),
                ),
                (
                    "weight",
                    1,
                    urwid.Filler(metadata_pile, valign="middle"),
                ),
            ]
        )

    def _create_default_album_art(self):
        """Create default album art placeholder."""
        placeholder = urwid.Text("♪\n\nNo Album Art\nAvailable", align="center")
        return placeholder

    def _show_placeholder(self):
        """Display the 'No Album Art Available' placeholder."""
        logger.info("Showing album art placeholder")
        placeholder = urwid.Text("♪\n\nNo Album Art\nAvailable", align="center")
        self.album_art_container = placeholder

        current_item = self.contents[0]
        linebox, (sizing, size) = current_item

        centered_placeholder = urwid.Padding(placeholder, align="center", width="pack")
        new_linebox = urwid.LineBox(urwid.Filler(centered_placeholder, valign="middle"))

        self.contents[0] = (new_linebox, (sizing, size))

    def update_track(self, song_filename):
        """Update the track info and album art."""
        logger.info(f"update_track called with: {song_filename}")

        if not song_filename:
            logger.warning("update_track called with empty song_filename")
            return

        self.filename_text.set_text(song_filename)
        logger.debug(f"Set filename text to: {song_filename}")

        try:
            if hasattr(state, "viewInfo"):
                logger.debug("state.viewInfo exists")

                song_index = None
                for i in range(state.viewInfo.songsLen()):
                    if state.viewInfo.songFileName(i) == song_filename:
                        song_index = i
                        break

                logger.debug(f"Found song_index: {song_index}")

                if song_index is not None:
                    title, album, artist, album_art = state.viewInfo.songInfo(
                        song_index
                    )
                    logger.debug(
                        f"Got metadata - Title: {title}, Album: {album}, Artist: {artist}"
                    )
                    self.title_text.set_text(title)
                    self.album_text.set_text(album)
                    self.artist_text.set_text(artist)
                else:
                    display_name = song_filename.replace(".mp3", "").replace("_", " ")
                    logger.debug(f"Using fallback display name: {display_name}")
                    self.title_text.set_text(display_name)
                    self.album_text.set_text("")
                    self.artist_text.set_text("")
            else:
                logger.error("state.viewInfo does not exist!")
        except Exception as e:
            logger.error(f"Exception in update_track metadata section: {e}")

            display_name = song_filename.replace(".mp3", "").replace("_", " ")
            self.title_text.set_text(display_name)
            self.album_text.set_text("")
            self.artist_text.set_text("")

        logger.info("Calling _update_album_art")
        self._update_album_art(song_filename)

    def _update_album_art(self, song_filename):
        """Update album art for the given track."""
        logger.info(f"_update_album_art called with: {song_filename}")

        try:
            if hasattr(state, "viewInfo"):
                full_path = f"{state.viewInfo.getDir()}/{song_filename}"
                logger.debug(f"Full path: {full_path}")

                apic_frame = ID3(full_path).get("APIC:Cover")
                if not apic_frame:
                    logger.info(f"No album art found in: {song_filename}")
                    self._show_placeholder()
                    return

                logger.info("Found album art! Checking cache...")
                image_data = apic_frame.data

                cached_ascii_art = _album_art_cache.get(full_path, image_data)
                if cached_ascii_art:
                    logger.info(f"Using cached album art for: {song_filename}")
                    ascii_art = cached_ascii_art
                else:
                    logger.info("Generating ASCII art from image...")
                    img = Image.open(BytesIO(image_data))
                    ImageFile.LOAD_TRUNCATED_IMAGES = True

                    ascii_art = convert_pil(img, is_unicode=True, width=80)
                    logger.debug(f"ASCII art length: {len(ascii_art)}")
                    logger.debug(f"ASCII art first 100 chars: {ascii_art[:100]}")
                    logger.debug(
                        f"ASCII art line count: {len(ascii_art.split(chr(10)))}"
                    )

                    _album_art_cache.set(full_path, image_data, ascii_art)

                cover_widget = ANSIWidget(ascii_art)

                if cover_widget:
                    logger.debug(f"self.contents length: {len(self.contents)}")
                    logger.debug(f"self.contents[0] type: {type(self.contents[0])}")
                    logger.debug(f"self.contents[0] content: {self.contents[0]}")

                    self.album_art_container = cover_widget

                    current_item = self.contents[0]
                    linebox, (sizing, size) = current_item

                    logger.debug(f"ANSIWidget type: {type(cover_widget)}")
                    logger.debug(f"ANSIWidget lines count: {len(cover_widget.lines)}")
                    logger.debug(
                        f"ANSIWidget first line: {cover_widget.lines[0] if cover_widget.lines else 'NO LINES'}"
                    )
                    logger.debug(
                        f"ANSIWidget display width: {cover_widget._display_width}"
                    )
                    logger.debug(f"ANSIWidget pack() returns: {cover_widget.pack()}")
                    logger.debug(
                        f"ANSIWidget lines after filtering: {len(cover_widget.lines)}"
                    )

                    centered_cover = urwid.Padding(
                        cover_widget, align="center", width="pack"
                    )
                    new_linebox = urwid.LineBox(
                        urwid.Filler(centered_cover, valign="middle")
                    )

                    self.contents[0] = (new_linebox, (sizing, size))
                    logger.info(
                        "Successfully updated album art widget (direct replacement)"
                    )
            else:
                logger.error("state.viewInfo does not exist in _update_album_art!")

        except Exception as e:
            logger.error(f"Exception in _update_album_art: {e}")
            error_widget = urwid.Text("Error loading\nalbum art", align="center")
            filler_widget = self.contents[0][0].original_widget
            filler_widget._w = error_widget
