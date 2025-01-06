import os

import urwid

from src.media import AudioPlayer
from src.singleton import BorgSingleton
from src.urwid_components.footer import Footer
from src.urwid_components.list import ListMod
from src.urwid_components.metadataEditorPop import MetadataEditor
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

    def __init__(self, change_view):
        self.walker = urwid.SimpleListWalker(self._generate_menu())
        self.song_list = ListMod(self.walker, self, change_view)
        self.metadata_editor = MetadataEditor(self.song_list, "pilaMetadata")

        state.pilaMetadata = self.metadata_editor

        self.audio_player = AudioPlayer()
        self.footer = Footer()
        self.info_panel = urwid.LineBox(self.metadata_editor, "Info")

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

        self.main_panel = urwid.LineBox(
            urwid.Pile([self.info_panel, self.youtube_panel])
        )
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
            self.walker.append(urwid.AttrMap(button, None, focus_map="reversed"))

        removed_songs = [
            song for song in state.viewInfo.canciones if song not in current_songs
        ]
        for song in removed_songs:
            state.viewInfo.deleteSong(song)
            for widget in self.walker:
                if widget.original_widget.get_label() == song:
                    self.walker.remove(widget)
                    break

    def _generate_menu(self):
        """Generate the initial menu of songs."""
        body = []
        for i in range(state.viewInfo.songsLen()):
            song_name = state.viewInfo.songFileName(i)
            button = urwid.Button(song_name)
            urwid.connect_signal(
                button, "click", self.change_focus, user_args=[song_name]
            )
            body.append(urwid.AttrMap(button, None, focus_map="reversed"))
        return body

    def change_focus(self, button, song_name):
        """Change focus between the song list and the main panel."""
        self.columns.focus_col = 1 if self.columns.focus_col == 0 else 0
