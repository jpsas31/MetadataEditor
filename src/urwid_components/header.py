import urwid

EDIT_MODE = "Edit"
VIEW_MODE = "View"


class Header(urwid.Pile):
    def __init__(self):
        self.mode = urwid.Text("", align="left")
        self.mode = urwid.AttrMap(self.mode, "Title")

        super().__init__(
            [
                self.mode,
            ]
        )

    def set_mode(self, text):
        if text == EDIT_MODE:
            self.set_attr("Notification")
        elif text == VIEW_MODE:
            self.set_attr("Title")


    def clear_status(self):
        """Clear status message."""
        self.mode.set_text("")

    def set_attr(self, attr):
        self.mode.set_attr_map({None: attr})
