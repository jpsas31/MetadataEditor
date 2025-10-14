import urwid

from src.singleton import BorgSingleton
from src.urwid_components.display import Display
from src.urwid_components.list import ListMod

state = BorgSingleton()


class ViewManager:
    """Manages different views in the application."""

    def __init__(self, change_view_callback, audio_player=None):
        self.change_view_callback = change_view_callback
        self._widget_map = {}
        self.audio_player = audio_player
        self.views = {}
        self.view_order = []
        self.displays = []
        self._initialize_views()

    def _initialize_views(self):
        """Initialize all application views."""
        from src.urwid_components.footer import Footer

        shared_footer = Footer()
        shared_walker = urwid.SimpleListWalker(self._generate_menu())
        self.shared_song_list = ListMod(shared_walker, self.change_view_callback)

        display = Display(
            audio_player=self.audio_player,
            footer=shared_footer,
            song_list=self.shared_song_list,
            widget_map=self._widget_map,
        )
        self.displays.append(display)
        self.add_view("main", display.frame, "Main View")

        simple_display = Display(
            audio_player=self.audio_player,
            footer=shared_footer,
            song_list=self.shared_song_list,
            widget_map=self._widget_map,
        )

        from src.urwid_components.simpleTrackInfo import SimpleTrackInfo

        simple_track_info = SimpleTrackInfo()

        simple_info_panel = urwid.LineBox(simple_track_info, "Track Info")

        simple_columns = urwid.Columns(
            [urwid.LineBox(simple_display.song_list, "Canciones"), simple_info_panel],
            dividechars=4,
        )
        simple_frame = urwid.Frame(simple_columns, footer=simple_display.footer)
        self.displays.append(simple_display)
        simple_display.simple_track_info = simple_track_info

        self.add_view("music", simple_frame, "Music Player")

    def add_view(self, key, widget, title=None):
        """Add a view to the manager."""
        self.views[key] = {"widget": widget, "title": title or key.title()}
        if key not in self.view_order:
            self.view_order.append(key)

    def get_view(self, key):
        """Get a view by key."""
        return self.views.get(key, {}).get("widget")

    def get_view_by_index(self, index):
        """Get a view by index."""
        if 0 <= index < len(self.view_order):
            key = self.view_order[index]
            self.shared_song_list.set_display(self.displays[index])
            return self.views[key]["widget"]
        return None

    def get_view_count(self):
        """Get the total number of views."""
        return len(self.view_order)

    def get_view_titles(self):
        """Get list of view titles in order."""
        return [self.views[key]["title"] for key in self.view_order]

    def get_initial_view(self):
        """Get the initial view to display."""
        return self.get_view_by_index(0)

    def _generate_menu(self):
        """Generate the initial menu of songs."""
        body = []
        for i in range(state.viewInfo.songsLen()):
            song_name = state.viewInfo.songFileName(i)
            button = urwid.Button(song_name)
            urwid.connect_signal(
                button, "click", self.change_view_callback, user_args=[song_name]
            )
            widget = urwid.AttrMap(button, None, focus_map="reversed")
            body.append(widget)

            self._widget_map[song_name] = widget

        return body
