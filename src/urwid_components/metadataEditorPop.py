import os
import threading

import urwid
from climage import convert, convert_pil

import src.tagModifier as tagModifier
from src.singleton import BorgSingleton
from src.urwid_components.ansiWidget import ANSIWidget
from src.urwid_components.editorBox import EditorBox
from src.urwid_components.popupMenu import CascadingBoxes, popup

state = BorgSingleton()


class MetadataEditor(CascadingBoxes):
    def __init__(self, song_list, top_widget_name):
        self.song_list = song_list
        self.modifier = None
        self.fill_progress = urwid.ProgressBar("normal", "complete")
        self._update_modifier()
        self._initialize_ui(top_widget_name)
        super().__init__(self.contents)

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
            self._create_button("View Cover", self.view_cover),
            self._create_button("Auto-fill Fields", self.fill_fields),
            popup(
                "View Cover",
                [self.get_cover()],
                lambda: 0,
                top_widget_name,
            ),
            popup(
                "Auto-fill for All Songs",
                [self.fill_progress],
                self.automatic_cover,
                top_widget_name,
            ),
            # urwid.AttrMap(self.get_cover(), "Title"),
        ]

        # self._connect_signals()
        # self._update_ui_with_metadata(state.viewInfo.songFileName(0))

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

    def get_cover(self):
        img = self.modifier.get_cover()
        if img is not None:
            ansi = ANSIWidget(convert_pil(img, is_unicode=True, width=60))
            body = urwid.Pile([ansi])
            return body
        return urwid.Filler(urwid.Text("No Album Cover Found"))

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
        title, album, artist, album_art = state.viewInfo.songInfo(
            self.song_list.focus_position
        )

        self.contents[1].set_text(file_name)
        self.contents[3].set_edit_text(title or "")
        self.contents[5].set_edit_text(album or "")
        self.contents[7].set_edit_text(artist or "")
        self.contents[8].original_widget.set_label(album_art)

    def view_cover(self, _widget=None):
        self._update_modifier()
        self.modifier.show_album_cover()

    def set_cover(self, _widget=None, file_name=None):
        self._update_modifier(file_name)
        title, album, artist, album_art = self.modifier.song_info()

        if album_art == "Has cover":
            self.modifier.remove_album_cover()
            self.contents[8].original_widget.set_label("Cover Removed")
        else:
            self.modifier.set_cover_from_spotify(state.viewInfo.getDir(), file_name)
            _, _, _, album_art = self.modifier.song_info()
            self.contents[8].original_widget.set_label(album_art)

    def edit_handler(self, widget, text):
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

    def fill_fields(self, _widget=None, file_name=None):
        self._update_modifier(file_name)
        self.modifier.fill_metadata_from_spotify()
        self._update_ui_with_metadata(self.modifier.file_path)

    def automatic_cover(self, _widget=None):
        threading.Thread(target=self._automatic_cover, daemon=True).start()

    def _automatic_cover(self):
        lock = threading.Lock()
        size = state.viewInfo.songsLen()

        for i in range(size):
            file_name = state.viewInfo.songFileName(i)
            self._update_modifier(file_name)
            self.modifier.fill_metadata_from_spotify(show_cover=False)

            with lock:
                self.fill_progress.set_completion(100 / size)

        self.original_widget = self.original_widget[0]
        self.box_level -= 1

    def test(self, _widget=None):
        pass
