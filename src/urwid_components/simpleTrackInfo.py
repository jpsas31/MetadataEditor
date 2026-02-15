from io import BytesIO

import urwid
from climage import convert_pil
from mutagen.id3 import ID3
from PIL import Image, ImageFile

from src.albumArtCache import AlbumArtCache
from src.urwid_components.ansiText import ANSIText


class SimpleTrackInfo(urwid.Pile):
    """Simple component with album art on top and track info below."""

    def __init__(self, view_info=None):
        self.view_info = view_info
        self.album_art_container = self._create_default_album_art()

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
        centered_placeholder = urwid.Padding(placeholder, align="center", width="pack")

        return urwid.Filler(centered_placeholder, valign="middle")

    def _show_placeholder(self):
        """Display the 'No Album Art Available' placeholder."""
        placeholder = self._create_default_album_art()
        self.album_art_container = placeholder

        current_item = self.contents[0]
        linebox, (sizing, size) = current_item

        self.contents[0] = (placeholder, (sizing, size))

    def update_track(self, song_filename):
        """Update the track info and album art."""
        if not song_filename:
            return

        self.filename_text.set_text(song_filename)

        try:
            if hasattr(self.view_info, "songs_len"):
                song_index = None
                for i in range(self.view_info.songs_len()):
                    if self.view_info.song_file_name(i) == song_filename:
                        song_index = i
                        break

                if song_index is not None:
                    title, album, artist, album_art = self.view_info.song_info(song_index)
                    self.title_text.set_text(title)
                    self.album_text.set_text(album)
                    self.artist_text.set_text(artist)
                else:
                    display_name = song_filename.replace(".mp3", "").replace("_", " ")
                    self.title_text.set_text(display_name)
                    self.album_text.set_text("")
                    self.artist_text.set_text("")

        except Exception:
            display_name = song_filename.replace(".mp3", "").replace("_", " ")
            self.title_text.set_text(display_name)
            self.album_text.set_text("")
            self.artist_text.set_text("")

        self._update_album_art(song_filename)

    def _update_album_art(self, song_filename):
        """Update album art for the given track."""
        if self.size is None:
            return
        try:
            full_path = f"{self.view_info.get_dir()}/{song_filename}"

            apic_frame = ID3(full_path).get("APIC:Cover")
            if not apic_frame:
                self._show_placeholder()
                return

            image_data = apic_frame.data

            album_art_size = 20 + int(min(self.size[0], self.size[1]))
            cached_ascii_art = self._album_art_cache.get(full_path, image_data, album_art_size)

            if cached_ascii_art:
                ascii_art = cached_ascii_art
            else:
                img = Image.open(BytesIO(image_data))
                ImageFile.LOAD_TRUNCATED_IMAGES = True
                ascii_art = convert_pil(img, is_unicode=True, width=album_art_size)

                self._album_art_cache.set(full_path, image_data, ascii_art, album_art_size)

            cover_widget = ANSIText(ascii_art, wrap=urwid.WrapMode.CLIP)

            self.album_art_container = cover_widget

            current_item = self.contents[0]
            linebox, (sizing, size) = current_item

            centered_cover = urwid.Padding(cover_widget, align="center", width="pack")

            new_linebox = urwid.Filler(centered_cover, valign="middle")

            self.contents[0] = (new_linebox, (sizing, size))

        except Exception as e:
            error_widget = urwid.Text("Error loading\nalbum art", align="center")
            filler_widget = self.contents[0][0].original_widget
            filler_widget._w = error_widget
