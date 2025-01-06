from datetime import timedelta

import urwid

from src.singleton import BorgSingleton
from src.urwid_components.mediaControls import MediaProgressBar

state = BorgSingleton()


class Footer(urwid.Pile):
    def __init__(self):
        self.music_bar = MediaProgressBar("normal", "complete")
        self.title = urwid.Text("", align="center")
        super().__init__(
            [
                urwid.AttrMap(
                    self.title,
                    "Title",
                ),
                self.music_bar,
            ]
        )

    def set_text(self, text):
        self.title.set_text(text)
