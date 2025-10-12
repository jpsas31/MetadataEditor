import os

import urwid

from src.singleton import BorgSingleton

state = BorgSingleton()


class ListMod(urwid.ListBox):
    def __init__(self, body, display, changeView):
        super().__init__(body)
        self.display = display
        self.changeView = changeView

    def keypress(self, size, key):
        cursor_pos = self.get_focus()[1]
        self._handle_keypress(key, cursor_pos)
        super().keypress(size, key)

    def _handle_keypress(self, key, cursor_pos):
        """
        Handle keyboard shortcuts for navigation and media controls.

        Navigation:
            up/down: Move focus
            right: Focus metadata panel
            1/2/3: Switch views
            esc: Exit

        Playback:
            s: Play/Pause toggle
            a: Play selected song
            p: Stop playback
            n: Next song
            b: Previous song (back)

        Loop:
            l: Toggle loop mode

        Other:
            delete: Delete song
        """
        player = self.display.audio_player

        # Navigation
        if key == "down":
            self._move_focus(cursor_pos + 1)
        elif key == "up":
            self._move_focus(cursor_pos - 1)
        elif key == "right":
            self.display.columns.focus_col = 1
        elif key == "esc":
            state.stop_event.set()
            raise urwid.ExitMainLoop()
        elif key in "123":
            try:
                self.changeView(int(key) - 1)
            except StopIteration:
                raise urwid.ExitMainLoop()

        # File operations
        elif key == "delete":
            self._delete_song(cursor_pos)

        # Playback controls
        elif key == "s":
            player.resume_pause()
        elif key == "a":
            self._play_song(cursor_pos)
        elif key == "p":
            player.stop()
        elif key == "n":
            self._play_next_song(cursor_pos)
        elif key == "b":
            self._play_previous_song(cursor_pos)

        # Volume controls
        elif key in ("+", "="):
            current_vol = player.get_volume()
            player.set_volume(min(1.0, current_vol + 0.1))
            self._show_volume_feedback()
        elif key == "-":
            current_vol = player.get_volume()
            player.set_volume(max(0.0, current_vol - 0.1))
            self._show_volume_feedback()
        elif key == "0":
            player.set_volume(0.0)
            self._show_volume_feedback()
        elif key == "m":
            # Toggle mute
            if player.get_volume() > 0:
                self._last_volume = player.get_volume()
                player.set_volume(0.0)
            else:
                player.set_volume(getattr(self, "_last_volume", 1.0))
            self._show_volume_feedback()

        # Loop control
        elif key == "l":
            player.set_loop(not player.get_loop())
            self._show_loop_feedback()

    def _show_volume_feedback(self):
        """Show volume level in footer (temporary feedback)."""
        if hasattr(self.display, "footer"):
            volume = int(self.display.audio_player.get_volume() * 100)
            status = "🔇 Muted" if volume == 0 else f"🔊 Volume: {volume}%"
            self.display.footer.set_status(status)

            import threading

            def clear_status():
                import time

                time.sleep(2)
                if hasattr(self.display, "footer"):
                    self.display.footer.clear_status()

            threading.Thread(target=clear_status, daemon=True).start()

    def _show_loop_feedback(self):
        """Show loop mode status in footer (temporary feedback)."""
        if hasattr(self.display, "footer"):
            loop_enabled = self.display.audio_player.get_loop()
            status = "🔁 Loop: ON" if loop_enabled else "🔁 Loop: OFF"
            self.display.footer.set_status(status)

            import threading

            def clear_status():
                import time

                time.sleep(2)
                if hasattr(self.display, "footer"):
                    self.display.footer.clear_status()

            threading.Thread(target=clear_status, daemon=True).start()

    def _move_focus(self, new_pos):
        if 0 <= new_pos < len(self.body):
            title, album, artist, album_art = state.viewInfo.songInfo(new_pos)
            self._update_metadata_panel(new_pos, title, album, artist, album_art)

    def _delete_song(self, pos):
        file_name = state.viewInfo.songFileName(pos)
        if os.path.isfile(file_name):
            os.remove(file_name)
            self.display._update_song_list()

    def _play_song(self, pos):
        """Play song at the given position and update footer."""
        file_name = state.viewInfo.songFileName(pos)
        self.display.audio_player.set_media(file_name)

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

        self.display.footer.set_text(display_text)

    def _play_next_song(self, current_pos):
        """Play the next song in the list."""
        next_pos = current_pos + 1
        if next_pos < state.viewInfo.songsLen():
            self.set_focus(next_pos)

            title, album, artist, album_art = state.viewInfo.songInfo(next_pos)
            self._update_metadata_panel(next_pos, title, album, artist, album_art)

            self._play_song(next_pos)
        else:
            if hasattr(self.display, "footer"):
                self.display.footer.set_status("📜 End of playlist")
                import threading

                def clear_status():
                    import time

                    time.sleep(2)
                    if hasattr(self.display, "footer"):
                        self.display.footer.clear_status()

                threading.Thread(target=clear_status, daemon=True).start()

    def _play_previous_song(self, current_pos):
        """Play the previous song in the list."""
        prev_pos = current_pos - 1
        if prev_pos >= 0:
            self.set_focus(prev_pos)

            title, album, artist, album_art = state.viewInfo.songInfo(prev_pos)
            self._update_metadata_panel(prev_pos, title, album, artist, album_art)

            self._play_song(prev_pos)
        else:
            if hasattr(self.display, "footer"):
                self.display.footer.set_status("📜 Start of playlist")
                import threading

                def clear_status():
                    import time

                    time.sleep(2)
                    if hasattr(self.display, "footer"):
                        self.display.footer.clear_status()

                threading.Thread(target=clear_status, daemon=True).start()

    def _update_metadata_panel(self, pos, title, album, artist, album_art):
        if hasattr(self.display, "metadata_editor"):
            self.display.metadata_editor.contents[1].set_text(
                state.viewInfo.songFileName(pos)
            )
            self.display.metadata_editor.contents[3].set_edit_text(title)
            self.display.metadata_editor.contents[5].set_edit_text(album)
            self.display.metadata_editor.contents[7].set_edit_text(artist)
            self.display.metadata_editor.contents[8].original_widget.set_label(
                album_art
            )

        if hasattr(self.display, "simple_track_info"):
            song_filename = state.viewInfo.songFileName(pos)
            self.display.simple_track_info.update_track(song_filename)
