import urwid

from src.urwid_components.mediaControls import MediaProgressBar


class Footer(urwid.Pile):
    def __init__(self):
        self.music_bar = MediaProgressBar("normal", "complete")
        self.title = urwid.Text("", align="center")
        self.status_text = urwid.Text("", align="center")
        super().__init__(
            [
                urwid.AttrMap(
                    self.title,
                    "Title",
                ),
                self.status_text,
                self.music_bar,
            ]
        )

    def set_text(self, text):
        self.title.set_text(text)

    def set_status(self, text):
        """Set status message (for batch operations, etc)."""
        self.status_text.set_text(text)

    def clear_status(self):
        """Clear status message."""
        self.status_text.set_text("")
