import urwid


class HelpDialog:
    scope_descriptions = {
        "global": "Works anywhere",
        "list": "Works when focus is on the song list",
    }

    def __init__(self, keybinds_config, on_okay):
        # Header
        header_text = urwid.Text(("banner", "Help"), align="center")
        header = urwid.AttrMap(header_text, "banner")

        # Body
        body_text = urwid.Text(self.format_keybinds_config(keybinds_config), align="center")

        body_scroller = urwid.ScrollBar(urwid.ListBox([body_text]))
        body = urwid.LineBox(body_scroller)
        self.on_okay = on_okay
        footer = urwid.Text("Press Enter to close", align="center")

        self.layout = urwid.Frame(body, header=header, footer=footer, focus_part="body")
        self.layout.keypress = self.handle_keypress

    def handle_keypress(self, size, key):
        if key == "enter":
            self.on_okay(None)
            return None

        return urwid.Frame.keypress(self.layout, size, key)

    def format_keybinds_config(self, keybinds_config):
        scopes = keybinds_config.keys()
        scope_text = [("normal", "Keybinds Configuration\n\n")]
        for scope in scopes:
            scope_text.append(("normal", f"{scope.upper()} - {self.scope_descriptions[scope]}\n"))
            for key, value in keybinds_config[scope].items():
                scope_text.append(("title", f"  {key}: {value}\n"))
            scope_text.append(("normal", "\n"))
        return scope_text
