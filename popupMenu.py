import urwid

from singleton import BorgSingleton
state = BorgSingleton()
palette = [
    ("Title", "black", "light blue"),
    ("streak", "black", "dark red"),
    ("bg", "black", "dark blue"),
    ("reversed", "standout", ""),
    ("normal", "black", "light blue"),
    ("complete", "black", "dark magenta"),
    ("reversed", "standout", ""),
]


def menu_button(caption, callback):
    button = urwid.Button(caption)
    urwid.connect_signal(button, "click", callback)
    return urwid.AttrMap(button, None, focus_map="reversed")


def popup(caption, choice, call, topWidget):
    contents = urwid.ListBox(urwid.SimpleFocusListWalker(choice))

    def open_menu(button):
        call()
        return getattr(state, topWidget).open_box(contents)

    return menu_button([caption, "..."], open_menu)


class CascadingBoxes(urwid.WidgetPlaceholder):
    max_box_levels = 4
    #
    def __init__(self, elements):
        self.contents = elements
        super(CascadingBoxes, self).__init__(
            urwid.ListBox(urwid.SimpleFocusListWalker(elements))
        )
        self.box_level = 0

    def open_box(self, box):
        self.original_widget = urwid.Overlay(
            urwid.LineBox(box),
            self.original_widget,
            align="center",
            width=("relative", 80),
            valign="middle",
            height=("relative", 80),
            min_width=24,
            min_height=8,
            left=self.box_level * 3,
            right=(self.max_box_levels - self.box_level - 1) * 3,
            top=self.box_level * 2,
            bottom=(self.max_box_levels - self.box_level - 1) * 2,
        )
        self.box_level += 1

    def keypress(self, size, key):
        if key == "esc" and self.box_level >= 1:
            self.original_widget = self.original_widget[0]
            self.box_level -= 1
        else:
            return super(CascadingBoxes, self).keypress(size, key)


