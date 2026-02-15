import logging
import queue
import threading

import urwid

from src.keybindsConfig import load_keybinds_config
from src.media import AudioPlayer

# from src.keyHandler import KeyHandler
from src.newkeyhandler import CTX_GLOBAL, KeyHandler
from src.urwid_components.viewManager import ViewManager
from src.viewInfo import ViewInfo

logging.basicConfig(
    filename="/tmp/album_art_debug.log",
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filemode="w",
)
logger = logging.getLogger(__name__)


class MainLoopManager:
    def __init__(self, dir):
        self.view_info = ViewInfo(dir)

        # Initialize KeyHandler first (without list_widget reference)
        self.key_handler = KeyHandler(config=load_keybinds_config())
        self.audio_player = AudioPlayer()
        self.initialize_key_handler()
        # Create ViewManager with KeyHandler
        self.view_manager = ViewManager(
            self.change_view, self.audio_player, self.key_handler, self.view_info
        )

        initial_view = self.view_manager.get_initial_view()
        self.loop = urwid.MainLoop(
            initial_view,
            palette=self._get_palette(),
            unhandled_input=self._unhandled_input,
        )

        main_view = self.view_manager.get_view("main")
        if main_view and hasattr(main_view, "footer") and hasattr(main_view.footer, "music_bar"):
            threading.Thread(
                target=self.audio_player.thread_play,
                args=[main_view.footer.music_bar.update_position],
            ).start()
        else:
            threading.Thread(
                target=self.audio_player.thread_play,
                args=[lambda sound_length, play_position: None],
            ).start()

        self._schedule_message_check()

    def initialize_key_handler(self):
        """Initialize the key handler."""
        self.key_handler.register_action("app_exit", self._handle_exit, needs_context=False)
        self.key_handler.register_action("show_help", self._handle_help, needs_context=False)
        self.key_handler.register_action(
            "view_switch_0", lambda: self.change_view(0), needs_context=False
        )
        self.key_handler.register_action(
            "view_switch_1", lambda: self.change_view(1), needs_context=False
        )
        self.key_handler.register_action(
            "view_switch_2", lambda: self.change_view(2), needs_context=False
        )

    def _unhandled_input(self, key):
        """Handle unhandled input at the top level."""
        if self.key_handler.handle_key(key, CTX_GLOBAL):
            return True
        return key

    def _get_palette(self):
        """Get the color palette for the application."""
        return [
            ("Title", "black", "light blue"),
            ("Notification", "black", "dark red"),
            ("streak", "black", "dark red"),
            ("bg", "black", "dark blue"),
            ("reversed", "standout", ""),
            ("normal", "black", "light blue"),
            ("complete", "black", "dark magenta"),
        ]

    def _schedule_message_check(self):
        self.loop.set_alarm_in(0.5, self._check_messages)

    def _check_messages(self, loop, *_args):
        view_index = self.view_manager.get_view_index("edit")
        main_display = self.view_manager.get_display_by_index(view_index)
        if main_display.should_update_song_list:
            loop.set_alarm_in(5, main_display._update_song_list)
        logger.info("Checking messages found")
        try:
            msg = main_display.youtube.message_queue.get_nowait()
            logger.info(f"Message: {msg}")
            if msg and main_display.text_info:
                main_display.text_info.set_text(msg)
        except queue.Empty:
            pass

        self._schedule_message_check()

    def change_view(self, index_or_song_name):
        if isinstance(index_or_song_name, str):
            song_name = index_or_song_name
            for i in range(self.view_info.songs_len()):
                if self.view_info.song_file_name(i) == song_name:
                    if hasattr(self.view_manager, "shared_song_list"):
                        song_list = self.view_manager.shared_song_list
                        song_list.set_focus(i)
                        title, album, artist, album_art = self.view_info.song_info(i)
                        song_list._update_metadata_panel(i, title, album, artist, album_art)
                    break
        else:
            index = index_or_song_name
            view = self.view_manager.get_view_by_index(index)
            if view:
                self.loop.widget = view

                self.loop.screen.clear()
                self.loop.draw_screen()

    def _handle_exit(self):
        """Handle exit key."""
        self.audio_player.stop_event.set()
        raise urwid.ExitMainLoop()

    def _handle_help(self):
        """Handle help key."""
        if hasattr(self, "view_manager"):
            main_view = self.view_manager.get_view("main")
            if main_view and hasattr(main_view, "footer"):
                main_view.footer.set_status("Press F1 for help | ESC to exit")

    def start(self):
        self.loop.run()
