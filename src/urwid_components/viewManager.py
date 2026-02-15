import logging

import urwid

from src.urwid_components.editorView import EditorView
from src.urwid_components.footer import Footer
from src.urwid_components.header import Header
from src.urwid_components.list import ListMod
from src.urwid_components.musicPlayerView import MusicPlayerView

logging.basicConfig(
    filename="/tmp/album_art_debug.log",
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filemode="w",
)
logger = logging.getLogger(__name__)


class ViewManager:
    """Manages different views in the application."""

    def __init__(self, change_view_callback, audio_player=None, key_handler=None, view_info=None):
        self.view_info = view_info
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
            self.view_info,
        )

        if self.key_handler:
            self.key_handler.list_widget = self.shared_song_list
            self.shared_song_list.key_handler = self.key_handler

        display = EditorView(
            audio_player=self.audio_player,
            footer=shared_footer,
            header=shared_header,
            song_list=self.shared_song_list,
            widget_map=self._widget_map,
            view_info=self.view_info,
        )

        simple_display = MusicPlayerView(
            audio_player=self.audio_player,
            footer=shared_footer,
            header=shared_header,
            song_list=self.shared_song_list,
            widget_map=self._widget_map,
            view_info=self.view_info,
        )

        self.add_view("music", simple_display.frame, "Music Player")
        self.displays.append(simple_display)
        self.add_view("edit", display.frame, "Main View")
        self.displays.append(display)

    def add_view(self, key, widget, title=None):
        """Add a view to the manager."""
        self.views[key] = {"widget": widget, "title": title or key.title()}
        if key not in self.view_order:
            self.view_order.append(key)

    def get_view(self, key):
        """Get a view by key."""
        return self.views.get(key, {}).get("widget")

    def get_view_index(self, key):
        """Get the index of a view by key."""
        return self.view_order.index(key)

    def get_display_by_index(self, index):
        """Get a display by index."""
        return self.displays[index]

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
                if self.view_info.songs_len() > 0:
                    pos = getattr(self.shared_song_list, "focus_position", 0)
                    if not isinstance(pos, int) or pos < 0 or pos >= self.view_info.songs_len():
                        pos = 0
                        self.shared_song_list.set_focus(pos)

                    title, album, artist, album_art = self.view_info.song_info(pos)
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
        for i in range(self.view_info.songs_len()):
            song_name = self.view_info.song_file_name(i)
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
