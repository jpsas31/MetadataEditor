import os

import urwid

from src.urwid_components.footer import Footer
from src.urwid_components.header import Header
from src.urwid_components.simpleTrackInfo import SimpleTrackInfo
from src.urwid_components.view import View
from src.youtube import Youtube


class MusicPlayerView(View):
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
        self.view_info = view_info
        self._widget_map = widget_map
        self.song_list = song_list
        self.song_list.set_display(self)
        self.should_update_song_list = False
        self.audio_player = audio_player
        self.youtube = Youtube(self)
        self.footer = footer if footer is not None else Footer()
        self.header = header if header is not None else Header()

        self.info_panel = SimpleTrackInfo(self.view_info)
        simple_columns = urwid.Columns(
            [urwid.LineBox(self.song_list), self.info_panel],
            dividechars=4,
        )
        self.frame = urwid.Frame(simple_columns, footer=self.footer)

        self.simple_track_info = self.info_panel

        self.columns = urwid.Columns(
            [urwid.LineBox(self.song_list), self.info_panel],
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

