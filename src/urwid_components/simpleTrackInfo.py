import logging
from io import BytesIO

import urwid
from climage import convert_pil
from mutagen.id3 import ID3
from PIL import Image, ImageFile

from src.albumArtCache import AlbumArtCache
from src.urwid_components.ansiWidget import ANSIWidget

logging.basicConfig(
    filename="/tmp/album_art_debug.log",
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filemode="w",
)
logger = logging.getLogger(__name__)


class SimpleTrackInfo(urwid.Pile):
    """Simple component with album art on top and track info below."""

    def __init__(self, view_info=None):
        logger.info("SimpleTrackInfo.__init__ called")
        self.view_info = view_info
        self.album_art_container = urwid.Text("♪\n\nNo Album Art\nAvailable", align="center")

        self.filename_text = urwid.Text("", align="center")
        self.title_text = urwid.Text("", align="center")
        self.album_text = urwid.Text("", align="center")
        self._album_art_cache = AlbumArtCache()
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

    def render(self, size, focus=False):
        self.size = size
        return super().render(size, focus)

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
            if hasattr(self.view_info, "songs_len"):
                song_index = None
                for i in range(self.view_info.songs_len()):
                    if self.view_info.song_file_name(i) == song_filename:
                        song_index = i
                        break

                logger.debug(f"Found song_index: {song_index}")

                if song_index is not None:
                    title, album, artist, album_art = self.view_info.song_info(song_index)
                    logger.debug(f"Got metadata - Title: {title}, Album: {album}, Artist: {artist}")
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
                logger.error("self.view_info does not exist!")
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
        if self.size is None:
            logger.warning("self.size is None, returning")
            return
        try:
            if hasattr(self.view_info, "get_dir"):
                full_path = f"{self.view_info.get_dir()}/{song_filename}"
                logger.debug(f"Full path: {full_path}")

                apic_frame = ID3(full_path).get("APIC:Cover")
                if not apic_frame:
                    logger.info(f"No album art found in: {song_filename}")
                    self._show_placeholder()
                    return

                logger.info("Found album art! Checking cache...")
                image_data = apic_frame.data

                album_art_size = 20 + int(min(self.size[0], self.size[1]))
                cached_ascii_art = self._album_art_cache.get(full_path, image_data, album_art_size)

                if cached_ascii_art:
                    logger.info(f"Using cached album art for: {song_filename}")
                    ascii_art = cached_ascii_art
                else:
                    logger.info("Generating ASCII art from image...")
                    img = Image.open(BytesIO(image_data))
                    ImageFile.LOAD_TRUNCATED_IMAGES = True
                    logger.debug(f"Image size: {img.size}")
                    logger.debug(f"component size: {self.size}")

                    logger.debug(f"chosen size: {album_art_size}")

                    ascii_art = convert_pil(img, is_unicode=True, width=album_art_size)

                    self._album_art_cache.set(full_path, image_data, ascii_art, album_art_size)

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
                        f"ANSIWidget first line: "
                        f"{cover_widget.lines[0] if cover_widget.lines else 'NO LINES'}"
                    )
                    logger.debug(f"ANSIWidget display width: {cover_widget._display_width}")
                    logger.debug(f"ANSIWidget pack() returns: {cover_widget.pack()}")
                    logger.debug(f"ANSIWidget lines after filtering: {len(cover_widget.lines)}")

                    centered_cover = urwid.Padding(cover_widget, align="center", width="pack")

                    new_linebox = urwid.Filler(centered_cover, valign="middle")

                    self.contents[0] = (new_linebox, (sizing, size))
                    logger.info("Successfully updated album art widget (direct replacement)")
            else:
                logger.error("self.view_info does not exist in _update_album_art!")

        except Exception as e:
            logger.error(f"Exception in _update_album_art: {e}")
            error_widget = urwid.Text("Error loading\nalbum art", align="center")
            filler_widget = self.contents[0][0].original_widget
            filler_widget._w = error_widget
