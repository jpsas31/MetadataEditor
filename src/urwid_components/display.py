import os

import urwid

from src.media import AudioPlayer
from src.singleton import BorgSingleton
from src.urwid_components.footer import Footer
from src.urwid_components.metadataEditor import MetadataEditor
from src.urwid_components.youtubeEdit import CustomEdit

state = BorgSingleton()


class Display:
    palette = [
        ("Title", "black", "light blue"),
        ("streak", "black", "dark red"),
        ("bg", "black", "dark blue"),
        ("reversed", "standout", ""),
        ("normal", "black", "light blue"),
        ("complete", "black", "dark magenta"),
    ]

    def __init__(self, audio_player=None, footer=None, song_list=None, widget_map=None):
        self._widget_map = widget_map
        self.song_list = song_list
        self.song_list.set_display(self)

        self.audio_player = audio_player if audio_player is not None else AudioPlayer()

        self.footer = footer if footer is not None else Footer()

        self.metadata_editor = MetadataEditor(
            self.song_list, "pilaMetadata", footer=self.footer
        )

        state.pilaMetadata = self.metadata_editor
        self.info_panel = urwid.LineBox(self.metadata_editor, "Info")

        # Make info_panel focusable
        def info_panel_keypress(size, key):
            return key

        self.info_panel.keypress = info_panel_keypress

        self.text_info = urwid.Text("")
        self.url_input = CustomEdit("Escribe link: ", parent=self, multiline=True)
        self.youtube_panel = urwid.LineBox(
            urwid.Pile(
                [
                    urwid.Filler(urwid.LineBox(self.url_input)),
                    urwid.Filler(urwid.LineBox(self.text_info, "")),
                ]
            ),
            "Youtubedl",
        )

        # Make youtube_panel focusable
        def youtube_panel_keypress(size, key):
            return key

        self.youtube_panel.keypress = youtube_panel_keypress

        # Create a focusable wrapper for the main panel
        class FocusablePile(urwid.Pile):
            def keypress(self, size, key):
                # Handle focus navigation within the pile
                if key in ("up", "down", "tab"):
                    # Let the parent Pile handle focus navigation
                    return super().keypress(size, key)
                # For other keys, just return them
                return key

        self.main_panel = FocusablePile([self.info_panel, self.youtube_panel])
        self.columns = urwid.Columns(
            [urwid.LineBox(self.song_list, "Canciones"), self.main_panel],
            dividechars=4,
        )
        self.frame = urwid.Frame(self.columns, footer=self.footer)

    def _update_song_list(self, *_args):
        """Update the song list based on the current directory."""
        current_songs = os.listdir(state.viewInfo.getDir())
        current_songs = [song for song in current_songs if song.endswith(".mp3")]

        new_songs = sorted(set(current_songs) - set(state.viewInfo.canciones))
        for song in new_songs:
            state.viewInfo.addSong(song)
            button = urwid.Button(song)
            urwid.connect_signal(button, "click", self.change_focus, user_args=[song])
            widget = urwid.AttrMap(button, None, focus_map="reversed")
            self.walker.append(widget)

            self._widget_map[song] = widget

        removed_songs = [
            song for song in state.viewInfo.canciones if song not in current_songs
        ]
        for song in removed_songs:
            state.viewInfo.deleteSong(song)

            if song in self._widget_map:
                self.walker.remove(self._widget_map[song])
                del self._widget_map[song]

    def _generate_menu(self):
        """Generate the initial menu of songs."""
        body = []
        for i in range(state.viewInfo.songsLen()):
            song_name = state.viewInfo.songFileName(i)
            button = urwid.Button(song_name)
            urwid.connect_signal(
                button, "click", self.change_focus, user_args=[song_name]
            )
            widget = urwid.AttrMap(button, None, focus_map="reversed")
            body.append(widget)

            self._widget_map[song_name] = widget
        return body

    def change_focus(self, button, song_name):
        """Change focus between the song list and the main panel."""

        for i in range(state.viewInfo.songsLen()):
            if state.viewInfo.songFileName(i) == song_name:
                title, album, artist, album_art = state.viewInfo.songInfo(i)
                self.song_list._update_metadata_panel(
                    i, title, album, artist, album_art
                )
                break

        self.columns.focus_col = 1 if self.columns.focus_col == 0 else 0
