import logging
import queue
import threading

import urwid

from src.media import AudioPlayer
from src.urwid_components.keyHandler import KeyHandler
from src.urwid_components.viewManager import ViewManager

logging.basicConfig(
    filename="/tmp/album_art_debug.log",
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filemode="w",
)
logger = logging.getLogger(__name__)


class MainLoopManager:
    def __init__(self, state):
        self.state = state

        self.audio_player = AudioPlayer()

        self.view_manager = ViewManager(self.change_view, self.audio_player, None)

        # Initialize KeyHandler after view_manager is created so we can access the list widget
        self.key_handler = KeyHandler(
            main_loop_manager=self, list_widget=self.view_manager.shared_song_list
        )

        # Update the view_manager's reference to the key_handler
        self.view_manager.key_handler = self.key_handler

        initial_view = self.view_manager.get_initial_view()
        self.loop = urwid.MainLoop(
            initial_view,
            palette=self._get_palette(),
            unhandled_input=self.input_handler,
        )

        main_view = self.view_manager.get_view("main")
        if (
            main_view
            and hasattr(main_view, "footer")
            and hasattr(main_view.footer, "music_bar")
        ):
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

    def _get_palette(self):
        """Get the color palette for the application."""
        return [
            ("Title", "black", "light blue"),
            ("streak", "black", "dark red"),
            ("bg", "black", "dark blue"),
            ("reversed", "standout", ""),
            ("normal", "black", "light blue"),
            ("complete", "black", "dark magenta"),
        ]

    def _schedule_message_check(self):
        self.loop.set_alarm_in(0.5, self._check_messages)

    def _check_messages(self, loop, *_args):
        if self.state.updateList:
            main_view = self.view_manager.get_view("main")
            if hasattr(main_view, "body") and hasattr(
                main_view.body, "_update_song_list"
            ):
                loop.set_alarm_in(5, main_view.body._update_song_list)

        try:
            msg = self.state.queueYt.get_nowait()

            main_view = self.view_manager.get_view("main")
            if hasattr(main_view, "body") and hasattr(main_view.body, "text_info"):
                main_view.body.text_info.set_text(msg)
        except queue.Empty:
            pass

        self._schedule_message_check()

    def change_view(self, index_or_song_name):
        if isinstance(index_or_song_name, str):
            song_name = index_or_song_name
            for i in range(self.state.viewInfo.songsLen()):
                if self.state.viewInfo.songFileName(i) == song_name:
                    if hasattr(self.view_manager, "shared_song_list"):
                        song_list = self.view_manager.shared_song_list
                        song_list.set_focus(i)
                        title, album, artist, album_art = self.state.viewInfo.songInfo(
                            i
                        )
                        song_list._update_metadata_panel(
                            i, title, album, artist, album_art
                        )
                    break
        else:
            index = index_or_song_name
            view = self.view_manager.get_view_by_index(index)
            if view:
                self.loop.widget = view

                self.loop.screen.clear()
                self.loop.draw_screen()

    def input_handler(self, key):
        logger.debug(f"Input handler: {key}")
        if isinstance(key, tuple) or isinstance(key, list):
            return

        # Use KeyHandler for global keys
        if hasattr(self, "key_handler") and self.key_handler.handle_key(key, "global"):
            return

        # Fallback for any keys not handled by KeyHandler
        if key == "esc":
            self.state.stop_event.set()
            raise urwid.ExitMainLoop()
        elif key.isdigit() and key in "123":
            index = int(key) - 1
            if 0 <= index < self.view_manager.get_view_count():
                self.change_view(index)

    def start(self):
        self.loop.run()
