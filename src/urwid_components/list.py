import os

import urwid

from src.singleton import BorgSingleton

state = BorgSingleton()


class ListMod(urwid.ListBox):
    def __init__(self, body, display, changeView):
        super().__init__(body)
        self.display = display
        self.changeView = changeView

    def keypress(self, size, key):
        cursor_pos = self.get_focus()[1]
        self._handle_keypress(key, cursor_pos)
        super().keypress(size, key)

    def _handle_keypress(self, key, cursor_pos):
        if key == "down":
            self._move_focus(cursor_pos + 1)
        elif key == "up":
            self._move_focus(cursor_pos - 1)
        elif key == "right":
            self.display.columns.focus_col = 1
        elif key == "delete":
            self._delete_song(cursor_pos)
        elif key == "s":
            self.display.audio_player.resume_pause()
        elif key == "a":
            self._play_song(cursor_pos)
        elif key == "esc":
            state.stop_event.set()
            raise urwid.ExitMainLoop()
        elif key in "123":
            try:
                self.changeView(int(key) - 1)
            except StopIteration:
                raise urwid.ExitMainLoop()

    def _move_focus(self, new_pos):
        if 0 <= new_pos < len(self.body):
            title, album, artist, album_art = state.viewInfo.songInfo(new_pos)
            self._update_metadata_panel(new_pos, title, album, artist, album_art)

    def _delete_song(self, pos):
        file_name = state.viewInfo.songFileName(pos)
        os.remove(file_name)
        self.display._update_song_list()

    def _play_song(self, pos):
        file_name = state.viewInfo.songFileName(pos)
        self.display.audio_player.set_media(file_name)
        self.display.footer.set_text(file_name)

    def _update_metadata_panel(self, pos, title, album, artist, album_art):
        self.display.metadata_editor.contents[1].set_text(
            state.viewInfo.songFileName(pos)
        )
        self.display.metadata_editor.contents[3].set_edit_text(title)
        self.display.metadata_editor.contents[5].set_edit_text(album)
        self.display.metadata_editor.contents[7].set_edit_text(artist)
        self.display.metadata_editor.contents[8].original_widget.set_label(album_art)
