import os
import threading

import urwid

import tagModifier
from popupMenu import CascadingBoxes, popup
from singleton import BorgSingleton

state = BorgSingleton()

class MetadaEditor(CascadingBoxes):
    def __init__(self, lista, topWidgetName):
        self.lista = lista
        self.modifier = tagModifier.MP3Editor(
            state.viewInfo.songFileName(self.lista.focus_position)
        )
        title, album, artist, albumArt = state.viewInfo.songInfo(0)
        self.fillProgress = urwid.ProgressBar("normal", "complete")
        super().__init__(
            [
                urwid.AttrMap(urwid.Text(str("File Name"), align="center"), "Title"),
                urwid.Text(state.viewInfo.songFileName(0), align="center"),
                urwid.AttrMap(urwid.Text(str("Title"), align="center"), "Title"),
                urwid.Edit(
                    caption="",
                    edit_text=str(title),
                    multiline=False,
                    align="center",
                    wrap="space",
                    allow_tab=False,
                    edit_pos=None,
                    layout=None,
                    mask=None,
                ),
                urwid.AttrMap(urwid.Text(str("Album"), align="center"), "Title"),
                urwid.Edit(
                    caption="",
                    edit_text=str(album),
                    multiline=False,
                    align="center",
                    wrap="space",
                    allow_tab=False,
                    edit_pos=None,
                    layout=None,
                    mask=None,
                ),
                urwid.AttrMap(urwid.Text(str("Artist"), align="center"), "Title"),
                urwid.Edit(
                    caption="",
                    edit_text=str(artist),
                    multiline=False,
                    align="center",
                    wrap="space",
                    allow_tab=False,
                    edit_pos=None,
                    layout=None,
                    mask=None,
                ),
                urwid.AttrMap(urwid.Button(albumArt), None, focus_map="reversed"),
                urwid.AttrMap(urwid.Button("Ver Cover"), None, focus_map="reversed"),
                urwid.AttrMap(
                    urwid.Button("Llenar Campos automaticamente"),
                    None,
                    focus_map="reversed",
                ),
                urwid.AttrMap(
                    urwid.Button("test"),
                    None,
                    focus_map="reversed",
                ),
                #  urwid.AttrMap(
                #     urwid.Button("Prueba"),
                #     None,
                #     focus_map="reversed",
                # ),
                popup(
                    "Llenar los campos de todas las canciones",
                    [self.fillProgress],
                    self.automatiCover,
                    topWidgetName,
                ),
            ]
        )
        urwid.connect_signal(self.contents[3], "change", self.editHandler)
        urwid.connect_signal(self.contents[5], "change", self.editHandler)
        urwid.connect_signal(self.contents[7], "change", self.editHandler)
        urwid.connect_signal(self.contents[8].original_widget, "click", self.setCover)
        urwid.connect_signal(self.contents[9].original_widget, "click", self.verCover)
        urwid.connect_signal(
            self.contents[10].original_widget, "click", self.llenarCampos
        )
        urwid.connect_signal(
            self.contents[11].original_widget, "click", self.automatiCover
        )

    def set_modifier(self, fileName=None):
        if fileName is None:
            fileName = state.viewInfo.canciones[self.lista.focus_position]
        if self.modifier.file_path != fileName:
            self.modifier = tagModifier.MP3Editor(fileName)

    def verCover(self, widget=None):
        self.set_modifier()
        self.modifier.show_album_cover()

    def setCover(self, wid=None, fileName=None):
        if fileName is None:
            fileName = state.viewInfo.canciones[self.lista.focus_position]
        self.set_modifier()
        title, album, artist, albumArt = self.modifier.song_info()
        if len(albumArt) == 0:
            self.modifier.set_cover_from_spotify(state.viewInfo.getDir(), fileName)
            title, album, artist, albumArt = self.modifier.song_info()

            if wid is not None:
                if len(albumArt) == 0:
                    wid.set_label("Cover no encontrada")
                else:
                    wid.set_label("Cover asignada")

        else:
            self.modifier.remove_album_cover()
            if wid is not None:
                wid.set_label("Cover eliminada")

    def editHandler(self, widget, text):
        if not os.path.isfile(state.viewInfo.songFileName(self.lista.focus_position)):
            return
        indexWidget = -1

        for j, i in enumerate(self.contents):
            if i == widget:
                indexWidget = j
                break

        modifier = tagModifier.MP3Editor(
            state.viewInfo.songFileName(self.lista.focus_position)
        )
       
        if indexWidget == 3:
            modifier.change_title(text)
        elif indexWidget == 5:
            modifier.change_album(text)
        elif indexWidget == 7:
            modifier.change_artist(text)

    def llenarCampos(self, widget=None, fileName=None):
        if fileName is None:
            fileName = state.viewInfo.songFileName(self.lista.focus_position)
        self.set_modifier(fileName)
        self.modifier.fill_metadata_from_spotify()
        title, album, artist, albumArt = state.viewInfo.songInfo(
            self.lista.focus_position
        )
        os.chdir(state.viewInfo.getDir())
        self.contents[1].set_text(str(fileName))
        self.contents[3].set_edit_text(str(title))
        self.contents[5].set_edit_text(str(album))
        self.contents[7].set_edit_text(str(artist))
        self.contents[8].original_widget.set_label(str(albumArt))
        if title is None or title != "None":
            self.contents[-3].original_widget.set_label("No se encontro la informacion")

    def automatiCover(self, w=None):
        threading.Thread(target=self._automatiCover, args=[]).start()

    def _automatiCover(self):
        size = state.viewInfo.songsLen()
        for i in range(size):
            fileName = state.viewInfo.songFileName(i)
            self.set_modifier(fileName)
            self.modifier.fill_metadata_from_spotify(show_cover=False)
            self.fillProgress.current += 100 / size
        self.original_widget = self.original_widget[0]
        self.box_level -= 1
