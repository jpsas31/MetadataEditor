import os
import queue
import threading
from queue import Queue

import urwid

import metadataEditorPop
import viewInfo
from media import AudioPlayer
from mediaControls import Footer
from singleton import BorgSingleton
from youtube import Youtube

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

    def __init__(self):
        self.walker = urwid.SimpleListWalker(self._generate_menu())
        self.song_list = self.ListMod(self.walker, self)
        self.metadata_editor = metadataEditorPop.MetadataEditor(
            self.song_list, "pilaMetadata"
        )

        state.pilaMetadata = self.metadata_editor

        self.audio_player = AudioPlayer()
        self.footer = Footer()
        self.info_panel = urwid.LineBox(self.metadata_editor, "Info")

        self.text_info = urwid.Text("")
        self.url_input = self.CustomEdit("Escribe link: ", parent=self, multiline=True)
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

        self.loop = urwid.MainLoop(
            self.frame, palette=self.palette, unhandled_input=self.exit
        )

        threading.Thread(
            target=self.audio_player.thread_play,
            args=[self.footer.music_bar.update_position],
        ).start()
        self._schedule_message_check()

    def _schedule_message_check(self):
        self.loop.set_alarm_in(0.5, self._check_messages)

    def _check_messages(self, loop, *_args):
        if state.updateList:
            loop.set_alarm_in(5, self._update_song_list)

        try:
            msg = state.queueYt.get_nowait()
            self.text_info.set_text(msg)
        except queue.Empty:
            pass
        self._schedule_message_check()

    def exit(self, key):
        if key == "esc":
            state.stop_event.set()
            raise urwid.ExitMainLoop()

    def _update_song_list(self, *_args):
        current_songs = os.listdir(state.viewInfo.getDir())
        current_songs = [song for song in current_songs if song.endswith(".mp3")]

        new_songs = sorted(set(current_songs) - set(state.viewInfo.canciones))
        for song in new_songs:
            state.viewInfo.addSong(song)
            button = urwid.Button(song)
            urwid.connect_signal(button, "click", self.change_focus, song)
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
        self.columns.focus_col = 1 if self.columns.focus_col == 0 else 0

    class CustomEdit(urwid.Edit):
        def __init__(self, caption="", edit_text="", multiline=False, parent=None):
            super().__init__(caption, edit_text, multiline)
            self.parent = parent
            self.youtube = Youtube()

        def set_edit_text(self, text):
            if text.endswith("\n"):
                self._download_url(text.strip())
                self.parent._update_song_list()
            else:
                super().set_edit_text(text)

        def _download_url(self, text):
            threading.Thread(
                target=self.youtube.youtube_descarga, args=[text], name="ydl_download"
            ).start()

    class ListMod(urwid.ListBox):
        def __init__(self, body, display):
            super().__init__(body)
            self.display = display

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
                self.display.exit(key)
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
            self.display.metadata_editor.contents[8].original_widget.set_label(
                album_art
            )


def main():
    # if len(sys.argv) <= 1:
    #     raise Warning("Provide a valid dir")
    # else:
    #     dir = sys.argv[1]
    dir = "."
    message_q = Queue()
    state.stop_event = threading.Event()
    state.viewInfo = viewInfo.ViewInfo(dir)
    state.queueYt = message_q
    state.updateList = False
    display = Display()

    display.loop.run()

    for th in threading.enumerate():
        if th != threading.current_thread():
            th.join()


if __name__ == "__main__":
    main()
