import os
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Semaphore

import urwid

import src.tagModifier as tagModifier
from src.singleton import BorgSingleton
from src.urwid_components.editorBox import EditorBox

state = BorgSingleton()


MUSICBRAINZ_RATE_LIMIT = Semaphore(4)
PARALLEL_WORKERS = 10


class MetadataEditor(urwid.WidgetPlaceholder):
    def __init__(self, song_list, top_widget_name, footer=None):
        self.song_list = song_list
        self.modifier = None
        self.footer = footer
        self.fill_progress = urwid.ProgressBar("normal", "complete")
        self._update_modifier()
        self._initialize_ui(top_widget_name)
        self.original_widget = urwid.ListBox(urwid.SimpleFocusListWalker(self.contents))

    def keypress(self, size, key):
        """Handle keypress events for the metadata editor."""
        # For now, just pass through to parent
        return super().keypress(size, key)

    def _initialize_ui(self, top_widget_name):
        self.contents = [
            self._create_title_widget("File Name"),
            self._create_text_widget(state.viewInfo.songFileName(0)),
            self._create_title_widget("Title"),
            self._create_edit_widget("", "title"),
            self._create_title_widget("Album"),
            self._create_edit_widget("", "album"),
            self._create_title_widget("Artist"),
            self._create_edit_widget("", "artist"),
            self._create_button("Set Cover", self.set_cover),
            self._create_button("Auto-fill Fields", self.fill_fields),
            self._create_button("Auto-fill for All Songs", self.automatic_cover),
        ]

    def _create_title_widget(self, text):
        return urwid.AttrMap(urwid.Text(text, align="center"), "Title")

    def _create_text_widget(self, text):
        return urwid.Text(text, align="center")

    def _create_edit_widget(self, initial_text, tag):
        return EditorBox(
            caption="",
            edit_text=initial_text,
            multiline=False,
            align="center",
            wrap="space",
            allow_tab=False,
            tag=tag,
            modifier=self.get_modifier,
        )

    def get_modifier(self):
        self._update_modifier()
        return self.modifier

    def _create_button(self, label, callback):
        return urwid.AttrMap(
            urwid.Button(label, on_press=callback), None, focus_map="reversed"
        )

    def _connect_signals(self):
        editable_indices = [3, 5, 7]
        for index in editable_indices:
            urwid.connect_signal(self.contents[index], "change", self.edit_handler)

    def _update_modifier(self, file_name=None):
        if file_name is None:
            file_name = state.viewInfo.songFileName(self.song_list.focus_position)
        if not self.modifier or self.modifier.file_path != file_name:
            self.modifier = tagModifier.MP3Editor(file_name)

    def _update_ui_with_metadata(self, file_name):
        if self.song_list.focus_position >= state.viewInfo.songsLen():
            return

        title, album, artist, album_art = state.viewInfo.songInfo(
            self.song_list.focus_position
        )

        if len(self.contents) > 8:
            self.contents[1].set_text(file_name)
            self.contents[3].set_edit_text(title or "")
            self.contents[5].set_edit_text(album or "")
            self.contents[7].set_edit_text(artist or "")
            self.contents[8].original_widget.set_label(album_art)

    def view_cover(self, _widget=None):
        try:
            self._update_modifier()
            self.modifier.show_album_cover()
        except Exception as e:
            print(f"Error viewing cover: {e}")

    def set_cover(self, _widget=None, file_name=None):
        try:
            self._update_modifier(file_name)
            title, album, artist, album_art = self.modifier.song_info()

            if album_art == "Has cover":
                self.modifier.remove_album_cover()
                if len(self.contents) > 8:
                    self.contents[8].original_widget.set_label("Cover Removed")
            else:
                self.modifier.set_cover_from_spotify(show_cover=False)
                _, _, _, album_art = self.modifier.song_info()
                if len(self.contents) > 8:
                    self.contents[8].original_widget.set_label(album_art)

            state.viewInfo.invalidate_cache(self.modifier.file_path)
        except Exception as e:
            print(f"Error setting cover: {e}")

    def edit_handler(self, widget, text):
        try:
            if self.song_list.focus_position >= state.viewInfo.songsLen():
                return

            file_name = state.viewInfo.songFileName(self.song_list.focus_position)
            if not os.path.isfile(file_name):
                return

            self._update_modifier(file_name)
            widget_index = self.contents.index(widget)

            textoInfo = self.contents[widget_index].get_edit_text()
            if widget_index == 3:
                self.modifier.change_title(textoInfo)
            elif widget_index == 5:
                self.modifier.change_album(textoInfo)
            elif widget_index == 7:
                self.modifier.change_artist(textoInfo)

            state.viewInfo.invalidate_cache(file_name)
        except Exception:
            pass

    def fill_fields(self, _widget=None, file_name=None):
        try:
            self._update_modifier(file_name)
            self.modifier.fill_metadata_from_spotify()
            self._update_ui_with_metadata(self.modifier.file_path)

            state.viewInfo.invalidate_cache(self.modifier.file_path)
        except Exception:
            pass

    def automatic_cover(self, _widget=None):
        threading.Thread(target=self._automatic_cover, daemon=True).start()

    def _process_single_track(self, index, file_name):
        """Process a single track. Returns (success, skipped, error_msg)."""
        try:
            modifier = tagModifier.MP3Editor(file_name)

            if modifier.has_metadata():
                return False, True, None

            with MUSICBRAINZ_RATE_LIMIT:
                modifier.fill_metadata_from_spotify(show_cover=False)

            state.viewInfo.invalidate_cache(file_name)

            return True, False, None
        except Exception as e:
            return False, False, str(e)

    def _automatic_cover(self):
        """Process all songs with parallel API requests (5-10x faster for bulk operations)."""
        import time

        try:
            size = state.viewInfo.songsLen()
            processed = 0
            skipped = 0
            completed = 0

            if self.footer:
                self.footer.set_status(f"Auto-fill: Starting... (0/{size})")

            tasks = [(i, state.viewInfo.songFileName(i)) for i in range(size)]

            with ThreadPoolExecutor(max_workers=PARALLEL_WORKERS) as executor:
                future_to_task = {
                    executor.submit(self._process_single_track, idx, fname): (
                        idx,
                        fname,
                    )
                    for idx, fname in tasks
                }

                for future in as_completed(future_to_task):
                    idx, file_name = future_to_task[future]
                    completed += 1

                    try:
                        success, was_skipped, error_msg = future.result()

                        if success:
                            processed += 1
                        elif was_skipped:
                            skipped += 1
                        elif error_msg:
                            print(f"Error processing {file_name}: {error_msg}")

                        progress = (completed * 100) / size
                        self.fill_progress.set_completion(progress)

                        if self.footer:
                            if error_msg:
                                self.footer.set_status(
                                    f"Auto-fill: Error on '{file_name}' - continuing... ({completed}/{size})"
                                )
                            else:
                                self.footer.set_status(
                                    f"Auto-fill: {completed}/{size} | Updated: {processed} | Skipped: {skipped}"
                                )
                    except Exception as e:
                        print(f"Error processing future for {file_name}: {e}")
                        continue

            if self.footer:
                self.footer.set_status(
                    f"✓ Auto-fill Complete: {processed} updated, {skipped} skipped"
                )

                time.sleep(5)
                self.footer.clear_status()

        except Exception as e:
            print(f"Error in automatic cover processing: {e}")
            if self.footer:
                self.footer.set_status(f"✗ Auto-fill Error: {e}")
