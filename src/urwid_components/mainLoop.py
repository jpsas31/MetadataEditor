import queue
import threading

import urwid

from src.media import AudioPlayer
from src.urwid_components.viewManager import ViewManager


class MainLoopManager:
    def __init__(self, state):
        self.state = state

        # Create audio player first
        self.audio_player = AudioPlayer()

        # Pass audio player to view manager
        self.view_manager = ViewManager(self.change_view, self.audio_player)

        initial_view = self.view_manager.get_initial_view()
        self.loop = urwid.MainLoop(
            initial_view, palette=self._get_palette(), unhandled_input=self.exit
        )

        # Start audio player thread with proper progress bar updates
        # Get the main display view to access its footer
        main_view = self.view_manager.get_view("main")
        if (
            main_view
            and hasattr(main_view, "footer")
            and hasattr(main_view.footer, "music_bar")
        ):
            # Connect audio player to the main view's music bar
            threading.Thread(
                target=self.audio_player.thread_play,
                args=[main_view.footer.music_bar.update_position],
            ).start()
        else:
            # Fallback: start thread without UI updates
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
            # Try to update song list in main view if available
            main_view = self.view_manager.get_view("main")
            if hasattr(main_view, "body") and hasattr(
                main_view.body, "_update_song_list"
            ):
                loop.set_alarm_in(5, main_view.body._update_song_list)

        try:
            msg = self.state.queueYt.get_nowait()
            # Try to update text info in main view if available
            main_view = self.view_manager.get_view("main")
            if hasattr(main_view, "body") and hasattr(main_view.body, "text_info"):
                main_view.body.text_info.set_text(msg)
        except queue.Empty:
            pass

        self._schedule_message_check()

    def change_view(self, index):
        view = self.view_manager.get_view_by_index(index)
        if view:
            self.loop.widget = view
            # Force a complete screen redraw to prevent corruption
            self.loop.screen.clear()
            self.loop.draw_screen()

    def exit(self, key):
        if isinstance(key, tuple):
            pass
        elif key == "esc":
            self.state.stop_event.set()
            raise urwid.ExitMainLoop()
        elif key in "123":
            try:
                index = int(key) - 1
                if 0 <= index < self.view_manager.get_view_count():
                    self.change_view(index)
            except StopIteration:
                raise urwid.ExitMainLoop()

    def start(self):
        self.loop.run()
