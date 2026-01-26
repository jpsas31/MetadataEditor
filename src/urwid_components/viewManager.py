import logging

import urwid

from src.singleton import BorgSingleton
from src.urwid_components.display import Display
from src.urwid_components.footer import Footer
from src.urwid_components.header import Header
from src.urwid_components.list import ListMod
from src.urwid_components.simpleTrackInfo import SimpleTrackInfo

logging.basicConfig(
    filename="/tmp/album_art_debug.log",
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filemode="w",
)
logger = logging.getLogger(__name__)

state = BorgSingleton()


class ViewManager:
    """Manages different views in the application."""

    def __init__(self, change_view_callback, audio_player=None, key_handler=None):
        self.change_view_callback = change_view_callback
        self._widget_map = {}
        self.audio_player = audio_player
        self.key_handler = key_handler
        self.views = {}
        self.view_order = []
        self.displays = []
        self._initialize_views()

    def _initialize_views(self):
        """Initialize all application views."""
        shared_header = Header()
        shared_footer = Footer()
        shared_walker = urwid.SimpleListWalker(self._generate_menu())
        self.shared_song_list = ListMod(
            shared_walker,
            self.change_view_callback,
            self.audio_player,
            self.key_handler,
        )

        if self.key_handler:
            self.key_handler.list_widget = self.shared_song_list
            self.shared_song_list.key_handler = self.key_handler

        display = Display(
            audio_player=self.audio_player,
            footer=shared_footer,
            header=shared_header,
            song_list=self.shared_song_list,
            widget_map=self._widget_map,
        )
        self.displays.append(display)
        self.add_view("main", display.frame, "Main View")

        simple_display = Display(
            audio_player=self.audio_player,
            footer=shared_footer,
            header=shared_header,
            song_list=self.shared_song_list,
            widget_map=self._widget_map,
        )
        simple_info_panel = SimpleTrackInfo()

        simple_columns = urwid.Columns(
            [urwid.LineBox(simple_display.song_list), simple_info_panel],
            dividechars=4,
        )
        simple_frame = urwid.Frame(simple_columns, footer=simple_display.footer)
        self.displays.append(simple_display)
        simple_display.simple_track_info = simple_info_panel

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
            logger.debug(f"Getting view by index: {index}")
            logger.debug(f"View order: {self.view_order}")
            logger.debug(f"Displays: {self.displays}")
            key = self.view_order[index]
            logger.debug(f"Key: {key}")
            self.shared_song_list.set_display(self.displays[index])
            logger.debug(f"Shared song list: {self.shared_song_list.display}")
            # Ensure the active display panels show metadata for the current/first item.
            try:
                if state.viewInfo.songs_len() > 0:
                    pos = getattr(self.shared_song_list, "focus_position", 0)
                    if not isinstance(pos, int) or pos < 0 or pos >= state.viewInfo.songs_len():
                        pos = 0
                        self.shared_song_list.set_focus(pos)

                    title, album, artist, album_art = state.viewInfo.song_info(pos)
                    self.shared_song_list._update_metadata_panel(
                        pos, title, album, artist, album_art
                    )
            except Exception as e:
                logger.exception("Error getting view by index")
                logger.error(f"Error: {e}")
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
        for i in range(state.viewInfo.songs_len()):
            song_name = state.viewInfo.song_file_name(i)
            button = urwid.Button(song_name)

            urwid.connect_signal(
                button,
                "click",
                lambda widget, name=song_name: self.change_view_callback(name),
            )
            widget = urwid.AttrMap(button, None, focus_map="reversed")
            body.append(widget)

            self._widget_map[song_name] = widget

        return body
