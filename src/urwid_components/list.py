import os
import threading
import time

import urwid

from src.newkeyhandler import CTX_LIST
from src.singleton import BorgSingleton

state = BorgSingleton()


class ListMod(urwid.ListBox):
    def __init__(self, body, changeView, audio_player=None, key_handler=None):
        super().__init__(body)
        self.display = None
        self.changeView = changeView
        self.audio_player = audio_player
        self.key_handler = key_handler
        self._last_volume = 1.0
        if self.key_handler:
            self.initialize_key_handler()

    def initialize_key_handler(self):
        """Initialize the key handler with context-aware actions."""
        self.key_handler.register_action(
            "nav_up", self._handle_navigation_up, needs_context=True
        )
        self.key_handler.register_action(
            "nav_down", self._handle_navigation_down, needs_context=True
        )
        self.key_handler.register_action(
            "nav_right", self._handle_focus_panel, needs_context=False
        )
        self.key_handler.register_action(
            "nav_left", self._handle_focus_list, needs_context=False
        )
        self.key_handler.register_action(
            "delete", self._delete_song, needs_context=True
        )

        self.key_handler.register_action(
            "playback_toggle", self._handle_playback_toggle, needs_context=False
        )
        self.key_handler.register_action(
            "playback_play", self._handle_playback_play, needs_context=True
        )
        self.key_handler.register_action(
            "playback_stop", self._handle_playback_stop, needs_context=False
        )
        self.key_handler.register_action(
            "playback_next", self._play_next_song, needs_context=True
        )
        self.key_handler.register_action(
            "playback_prev", self._play_previous_song, needs_context=True
        )
        self.key_handler.register_action(
            "volume_up", self._handle_volume_up, needs_context=False
        )
        self.key_handler.register_action(
            "volume_down", self._handle_volume_down, needs_context=False
        )
        self.key_handler.register_action(
            "volume_mute", self._handle_volume_mute, needs_context=False
        )
        self.key_handler.register_action(
            "volume_toggle_mute", self._handle_volume_toggle_mute, needs_context=False
        )
        self.key_handler.register_action(
            "loop_toggle", self._handle_loop, needs_context=False
        )

    def set_display(self, display):
        self.display = display

    def keypress(self, size, key):
        """Handle key press with context awareness."""
        focus_widget, cursor_pos = self.get_focus()

        context = {
            "cursor_pos": cursor_pos,
            "widget": self,
            "focus_widget": focus_widget,
            "size": size,
        }

        if self.key_handler and self.key_handler.handle_key(key, CTX_LIST, context):
            return

        return super().keypress(size, key)

    def _handle_navigation_up(self, context):
        """Handle up navigation with wrap-around."""
        cursor_pos = context.get("cursor_pos", 0)
        new_pos = cursor_pos - 1
        if new_pos < 0:
            new_pos = len(self.body) - 1
        self._move_focus(new_pos)

    def _handle_navigation_down(self, context):
        """Handle down navigation with wrap-around."""
        cursor_pos = context.get("cursor_pos", 0)
        new_pos = cursor_pos + 1
        if new_pos >= len(self.body):
            new_pos = 0
        self._move_focus(new_pos)

    def _handle_focus_panel(self):
        """Handle panel focusing."""
        if self.display and hasattr(self.display, "columns"):
            self.display.columns.focus_col = 1

    def _handle_focus_list(self):
        """Handle focusing back to song list."""
        if self.display and hasattr(self.display, "columns"):
            self.display.columns.focus_col = 0

    def _delete_song(self, context):
        """Delete song at cursor position."""
        cursor_pos = context.get("cursor_pos", 0)
        file_name = state.viewInfo.songFileName(cursor_pos)
        if os.path.isfile(file_name):
            os.remove(file_name)
            if self.display:
                self.display._update_song_list()

    def _handle_playback_toggle(self):
        """Toggle play/pause."""
        if self.audio_player:
            self.audio_player.resume_pause()

    def _handle_playback_play(self, context):
        """Play song at cursor position."""
        cursor_pos = context.get("cursor_pos", 0)
        self._play_song(cursor_pos)

    def _handle_playback_stop(self):
        """Stop playback."""
        if self.audio_player:
            self.audio_player.stop()

    def _handle_volume_up(self):
        """Increase volume."""
        if self.audio_player:
            current_vol = self.audio_player.get_volume()
            self.audio_player.set_volume(min(1.0, current_vol + 0.1))
            self._show_volume_feedback()

    def _handle_volume_down(self):
        """Decrease volume."""
        if self.audio_player:
            current_vol = self.audio_player.get_volume()
            self.audio_player.set_volume(max(0.0, current_vol - 0.1))
            self._show_volume_feedback()

    def _handle_volume_mute(self):
        """Mute volume."""
        if self.audio_player:
            self.audio_player.set_volume(0.0)
            self._show_volume_feedback()

    def _handle_volume_toggle_mute(self):
        """Toggle mute."""
        if self.audio_player:
            if self.audio_player.get_volume() > 0:
                self._last_volume = self.audio_player.get_volume()
                self.audio_player.set_volume(0.0)
            else:
                self.audio_player.set_volume(self._last_volume)
            self._show_volume_feedback()

    def _handle_loop(self):
        """Toggle loop mode."""
        if self.audio_player:
            self.audio_player.set_loop(not self.audio_player.get_loop())
            self._show_loop_feedback()

    def _show_volume_feedback(self):
        """Show volume level in footer (temporary feedback)."""
        if self.display and hasattr(self.display, "footer"):
            volume = int(self.audio_player.get_volume() * 100)
            status = "Muted" if volume == 0 else f"Volume: {volume}%"
            self.display.footer.set_status(status)

            def clear_status():
                time.sleep(2)
                if self.display and hasattr(self.display, "footer"):
                    self.display.footer.clear_status()

            threading.Thread(target=clear_status, daemon=True).start()

    def _show_loop_feedback(self):
        """Show loop mode status in footer (temporary feedback)."""
        if self.display and hasattr(self.display, "footer"):
            loop_enabled = self.audio_player.get_loop()
            status = "Loop: ON" if loop_enabled else "Loop: OFF"
            self.display.footer.set_status(status)

            def clear_status():
                time.sleep(2)
                if self.display and hasattr(self.display, "footer"):
                    self.display.footer.clear_status()

            threading.Thread(target=clear_status, daemon=True).start()

    def _move_focus(self, new_pos):
        """Move focus to new position and update metadata."""
        max_pos = len(self.body) - 1
        if new_pos > max_pos:
            new_pos = 0
        elif new_pos < 0:
            new_pos = max_pos

        if 0 <= new_pos <= max_pos:
            self.set_focus(new_pos)
            title, album, artist, album_art = state.viewInfo.songInfo(new_pos)
            self._update_metadata_panel(new_pos, title, album, artist, album_art)

    def _play_song(self, pos):
        """Play song at the given position and update footer."""
        file_name = state.viewInfo.songFileName(pos)
        self.audio_player.set_media(file_name)

        try:
            title, album, artist, _ = state.viewInfo.songInfo(pos)
            if title and artist:
                display_text = f"{title} - {artist}"
            elif title:
                display_text = title
            else:
                display_text = os.path.basename(file_name)
        except Exception:
            display_text = os.path.basename(file_name)

        if self.display and hasattr(self.display, "footer"):
            self.display.footer.set_text(display_text)

    def _play_next_song(self, context):
        """Play the next song in the list with wrap-around."""
        current_pos = context.get("cursor_pos", 0)
        next_pos = current_pos + 1
        max_pos = state.viewInfo.songsLen() - 1

        if next_pos > max_pos:
            next_pos = 0

        self.set_focus(next_pos)
        title, album, artist, album_art = state.viewInfo.songInfo(next_pos)
        self._update_metadata_panel(next_pos, title, album, artist, album_art)
        self._play_song(next_pos)

    def _play_previous_song(self, context):
        """Play the previous song in the list with wrap-around."""
        current_pos = context.get("cursor_pos", 0)
        prev_pos = current_pos - 1
        max_pos = state.viewInfo.songsLen() - 1

        if prev_pos < 0:
            prev_pos = max_pos

        self.set_focus(prev_pos)
        title, album, artist, album_art = state.viewInfo.songInfo(prev_pos)
        self._update_metadata_panel(prev_pos, title, album, artist, album_art)
        self._play_song(prev_pos)

    def _update_metadata_panel(self, pos, title, album, artist, album_art):
        """Update the metadata panel with song information."""
        if self.display and hasattr(self.display, "metadata_editor"):
            self.display.metadata_editor.contents[1].set_text(
                state.viewInfo.songFileName(pos)
            )
            self.display.metadata_editor.contents[3].set_edit_text(title)
            self.display.metadata_editor.contents[5].set_edit_text(album)
            self.display.metadata_editor.contents[7].set_edit_text(artist)
            self.display.metadata_editor.contents[8].original_widget.set_label(
                album_art
            )

        if self.display and hasattr(self.display, "simple_track_info"):
            song_filename = state.viewInfo.songFileName(pos)
            self.display.simple_track_info.update_track(song_filename)
