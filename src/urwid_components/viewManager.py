from io import BytesIO

import urwid
from climage import convert_pil
from mutagen.id3 import APIC, ID3
from PIL import Image, ImageFile

from src.singleton import BorgSingleton
from src.urwid_components.ansiWidget import ANSIWidget
from src.urwid_components.display import Display

state = BorgSingleton()


class ViewManager:
    """Manages different views in the application."""

    def __init__(self, change_view_callback, audio_player=None):
        self.change_view_callback = change_view_callback
        self.audio_player = audio_player
        self.views = {}
        self.view_order = []
        self._initialize_views()

    def _initialize_views(self):
        """Initialize all application views."""
        # Main display view (existing complex view)
        display = Display(self.change_view_callback, audio_player=self.audio_player)

        self.add_view("main", display.frame, "Main View")

        # Simple music view - create a modified display with simple track info
        simple_display = Display(
            self.change_view_callback, audio_player=self.audio_player
        )

        # Replace the metadata editor with simple track info
        from src.urwid_components.simpleTrackInfo import SimpleTrackInfo

        simple_track_info = SimpleTrackInfo()

        # Create simple info panel without YouTube panel
        simple_info_panel = urwid.LineBox(simple_track_info, "Track Info")

        # Create new columns with only the simple info panel (no YouTube panel)
        simple_columns = urwid.Columns(
            [urwid.LineBox(simple_display.song_list, "Canciones"), simple_info_panel],
            dividechars=4,
        )
        simple_frame = urwid.Frame(simple_columns, footer=simple_display.footer)

        # Store reference to simple track info for updates
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
