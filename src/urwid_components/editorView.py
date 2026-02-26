import os

import urwid

from src.urwid_components.ansiText import ANSIText
from src.urwid_components.metadataEditor import MetadataEditor
from src.urwid_components.view import View
from src.urwid_components.youtubeEdit import CustomEdit
from src.youtube import Youtube


class EditorView(View):
    def __init__(
        self,
        audio_player=None,
        footer=None,
        header=None,
        song_list=None,
        widget_map=None,
        view_info=None,
    ):
        super().__init__(audio_player, footer, header, song_list, widget_map, view_info)
        self._widget_map = widget_map
        self.song_list.set_display(self)
        self.should_update_song_list = False
        self.youtube = Youtube(self)

        self.metadata_editor = MetadataEditor(
            self.song_list, "pilaMetadata", footer=self.footer, view_info=self.view_info
        )

        self.info_panel = urwid.LineBox(self.metadata_editor)

        self.text_info = ANSIText("")
        self.url_input = CustomEdit(
            "Escribe link: ", parent=self, multiline=True, youtube=self.youtube
        )

        self.youtube_panel = urwid.LineBox(
            urwid.Pile(
                [
                    urwid.Filler(urwid.LineBox(self.url_input)),
                    # self.text_info,
                    urwid.Filler(urwid.LineBox(self.text_info)),
                ]
            ),
        )

        # Create a focusable wrapper for the main panel
        class FocusablePile(urwid.Pile):
            def keypress(self, size, key):
                # Allow switching between panels without stealing keys from children.
                if key in ("tab",):
                    self.focus_position = (self.focus_position + 1) % len(self.contents)
                    return None
                if key in ("shift tab", "backtab"):
                    self.focus_position = (self.focus_position - 1) % len(self.contents)
                    return None

                return super().keypress(size, key)

        self.main_panel = FocusablePile([self.info_panel, self.youtube_panel])
        self.columns = urwid.Columns(
            [urwid.LineBox(self.song_list), self.main_panel],
            dividechars=4,
        )
        self.frame = urwid.Frame(self.columns, header=self.header, footer=self.footer)

    def _update_song_list(self, *_args):
        """Update the song list based on the current directory."""
        current_songs = os.listdir(self.view_info.get_dir())
        current_songs = [song for song in current_songs if song.endswith(".mp3")]

        new_songs = sorted(set(current_songs) - set(self.view_info.canciones))
        for song in new_songs:
            self.view_info.add_song(song)
            button = urwid.Button(song)
            urwid.connect_signal(button, "click", self.change_focus, user_args=[song])
            widget = urwid.AttrMap(button, None, focus_map="reversed")
            self.song_list.walker.append(widget)

            self._widget_map[song] = widget

        removed_songs = [song for song in self.view_info.canciones if song not in current_songs]
        for song in removed_songs:
            self.view_info.delete_song(song)

            if song in self._widget_map:
                self.song_list.walker.remove(self._widget_map[song])
                del self._widget_map[song]

    def _generate_menu(self):
        """Generate the initial menu of songs."""
        body = []
        for i in range(self.view_info.songs_len()):
            song_name = self.view_info.song_file_name(i)
            button = urwid.Button(song_name)
            urwid.connect_signal(button, "click", self.change_focus, user_args=[song_name])
            widget = urwid.AttrMap(button, None, focus_map="reversed")
            body.append(widget)

            self._widget_map[song_name] = widget
        return body

    def change_focus(self, button, song_name):
        """Change focus between the song list and the main panel."""

        for i in range(self.view_info.songs_len()):
            if self.view_info.song_file_name(i) == song_name:
                title, album, artist, album_art = self.view_info.song_info(i)
                self.song_list._update_metadata_panel(i, title, album, artist, album_art)
                break

        self.columns.focus_col = 1 if self.columns.focus_col == 0 else 0
