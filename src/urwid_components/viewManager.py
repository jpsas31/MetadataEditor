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

    def __init__(self, audio_player=None, key_handler=None, view_info=None):
        self.view_info = view_info
        self._widget_map = {}
        self.audio_player = audio_player
        self.key_handler = key_handler
        self.views = {}
        self.view_order = []
        self._initialize_views()

    def _initialize_views(self):
        """Initialize all application views."""
        shared_header = Header()
        shared_footer = Footer()
        shared_walker = urwid.SimpleListWalker(self._generate_menu())
        self.shared_song_list = ListMod(
            shared_walker,
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

        background_view = urwid.Frame(
            urwid.SolidFill("▒"), header=shared_header, footer=shared_footer
        )

        self.add_view("music", simple_display, "Music Player")
        self.add_view("edit", display, "Main View")
        self.add_view("background", background_view, "Background")

    def add_view(self, key, widget, title=None):
        """Add a view to the manager."""
        self.views[key] = {"widget": widget, "title": title or key.title()}
        if key not in self.view_order:
            self.view_order.append(key)

    def get_view(self, key):
        """Get a view by key."""
        return self.views.get(key, {}).get("widget")

    def _generate_menu(self):
        """Generate the initial menu of songs."""
        body = []
        for i in range(self.view_info.songs_len()):
            song_name = self.view_info.song_file_name(i)
            text = urwid.Text(song_name)
            widget = urwid.AttrMap(text, None, focus_map="reversed")
            body.append(widget)

            self._widget_map[song_name] = widget

        return body
