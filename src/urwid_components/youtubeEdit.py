import threading

import urwid

from src.singleton import BorgSingleton
from src.youtube import Youtube

state = BorgSingleton()


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
