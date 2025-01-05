import logging
import os
import queue
import threading
from queue import Queue
import sys
import urwid

import metadataEditorPop
import viewInfo
from media import AudioPlayer
from mediaControls import Footer
from singleton import BorgSingleton
from youtube import Youtube



state = BorgSingleton()


class Display:
    palette = [
        ("Title", "black", "light blue"),
        ("streak", "black", "dark red"),
        ("bg", "black", "dark blue"),
        ("reversed", "standout", ""),
        ("normal", "black", "light blue"),
        ("complete", "black", "dark magenta"),
    ]

    def __init__(self):
        self.walker = urwid.SimpleListWalker(self.listMenu())
        self.lista = self.ListMod(self.walker, self)
        self.pilaMetadata = metadataEditorPop.MetadaEditor(self.lista, "pilaMetadata")

        state.pilaMetadata = self.pilaMetadata

        self.audio_player = AudioPlayer()
        self.footer = Footer()
        self.pila = self.pilaMetadata
        pilacomp = urwid.LineBox(self.pila, "Info")

        self.texto_info = urwid.Text("")
        editURL = self.CustomEdit("Escribe link: ", parent=self, multiline=True)
        textoDescarga = urwid.Filler(urwid.LineBox(editURL))
        texto_decorado = urwid.Filler(urwid.LineBox(self.texto_info, ""))
        self.pilaYoutube = urwid.LineBox(
            urwid.Pile([textoDescarga, texto_decorado]), "Youtubedl"
        )

        pila2 = [pilacomp, self.pilaYoutube]
        self.pilaPrincipal = urwid.LineBox(urwid.Pile(pila2))
        self.columns = urwid.Columns(
            [urwid.LineBox(self.lista, "Canciones"), self.pilaPrincipal],
            dividechars=4,
            focus_column=0,
            min_width=1,
            box_columns=None,
        )

        self.frame = urwid.Frame(self.columns, footer=self.footer)
        self.loop = urwid.MainLoop(
            self.frame,
            palette=self.palette,
            unhandled_input=self.exit,
            handle_mouse=False,
        )

        threading.Thread(
            target=self.audio_player.thread_play,
            args=[self.footer.music_bar.update_position],
        ).start()
        self.check_messages(self.loop, None)

    def check_messages(self, loop, *_args):
        loop.set_alarm_in(
            sec=0.5,
            callback=self.check_messages,
        )

        if state.updateList:
            loop.set_alarm_in(
                sec=5,
                callback=self.updateWalker,
            )
        try:
            msg = state.queueYt.get_nowait()
        except queue.Empty:
            return
        self.texto_info.set_text(msg)

    def exit(self, key):
        if key == "esc":
            state.stop_event.set()
            raise urwid.ExitMainLoop()

    def changeFocus(self, button, text):
        if self.columns.focus_col == 0:
            self.columns.focus_col = 1

    def updateWalker(self, a=None, b=None):
        canciones = os.listdir(state.viewInfo.getDir())
        canciones = [x for x in canciones if "mp3" in x]
        cancionesAgregar = list(set(canciones) - set(state.viewInfo.canciones))
        cancionesAgregar.sort()

        if len(cancionesAgregar) > 0:
            for cancion in cancionesAgregar:
                state.viewInfo.addSong(cancion)
                button = urwid.Button(cancion)
                urwid.connect_signal(button, "click", self.changeFocus, cancion)
                self.walker.append(urwid.AttrMap(button, None, focus_map="reversed"))
                self.walker[-1].original_widget.get_label()
                self.walker.sort(key=lambda x: x.original_widget.get_label())
        else:
            for cancion in range(state.viewInfo.songsLen()):
                if state.viewInfo.songFileName(cancion) not in canciones:
                    for widget in self.walker:
                        if (
                            widget.original_widget.get_label()
                            == state.viewInfo.songFileName(cancion)
                        ):
                            self.walker.remove(widget)
                            state.viewInfo.deleteSong(
                                widget.original_widget.get_label()
                            )
                            break
                    break

    def listMenu(self):
        body = []
        for i in range(state.viewInfo.songsLen()):
            cancion = state.viewInfo.songFileName(i)
            button = urwid.Button(cancion)
            urwid.connect_signal(button, "click", self.changeFocus, user_args=[cancion])
            body.append(urwid.AttrMap(button, None, focus_map="reversed"))
        return body

    class CustomEdit(urwid.Edit):
        def __init__(self, caption="", edit_text="", multiline=False, parent=None):
            super().__init__(caption, edit_text, multiline)
            self.parent = parent
            self.youtube = Youtube()

        def URLDownload(self, text):
            # threading.Thread(
            #     target=self.youtube.youtube_descarga,
            #     args=[text],
            #     name="ydl_download",
            # ).start()

            super().set_edit_text("")

        def set_edit_text(self, text):
            
            if text.endswith("\n"):
                self.URLDownload(text)
                self.parent.updateWalker()

            else:
                super().set_edit_text(text)

    class ListMod(urwid.ListBox):
        def __init__(self, body, display):
            self.display = display
            super().__init__(body)

        def keypress(self, size, key):
            cursorPos = self.get_focus()[1]

            self.display.pila.contents[-3].original_widget.set_label(
                "Llenar Campos automaticamente"
            )

            if key == "down":
                if self.focus is not None:
                    cursorPos = cursorPos + 1
                    if cursorPos >= len(self.body):
                        cursorPos -= 1
            elif key == "up":
                if self.focus is not None:
                    cursorPos = cursorPos - 1
                    if cursorPos < 0:
                        cursorPos = 0
            elif key == "right":
                if self.display.columns.focus_col == 0:
                    self.display.columns.focus_col = 1
            elif key == "esc":
                state.stop_event.set()
                self.display.exit(key)
                raise urwid.ExitMainLoop()

            elif key == "delete":
                os.remove(state.viewInfo.songFileName(cursorPos))
                self.display.updateWalker()
                cursorPos = self.get_focus()[1]

                title, album, artist, albumArt = state.viewInfo.songInfo(cursorPos)

                os.chdir(state.viewInfo.dir)
                self.display.pila.contents[1].set_text(
                    str(state.viewInfo.songFileName(cursorPos))
                )
                self.display.pila.contents[3].set_edit_text(str(title))
                self.display.pila.contents[5].set_edit_text(str(album))
                self.display.pila.contents[7].set_edit_text(str(artist))
                self.display.pila.contents[8].original_widget.set_label(str(albumArt))
            elif key == "s":
                if self.focus is not None:
                    self.display.audio_player.resume_pause()
            elif key == "a":
                if self.focus is not None:
                    self.display.audio_player.set_media(
                        state.viewInfo.songFileName(cursorPos)
                    )
                    self.display.footer[0].set_text(
                        state.viewInfo.songFileName(cursorPos)
                    )

            if cursorPos is None:
                super().keypress(size, key)
                return

            if key in {"down", "up"} and cursorPos < len(self.body):
                title, album, artist, albumArt = state.viewInfo.songInfo(cursorPos)
                os.chdir(state.viewInfo.dir)
                self.display.pila.contents[1].set_text(
                    str(state.viewInfo.songFileName(cursorPos))
                )
                self.display.pila.contents[3].set_edit_text(str(title))
                self.display.pila.contents[5].set_edit_text(str(album))
                self.display.pila.contents[7].set_edit_text(str(artist))
                self.display.pila.contents[8].original_widget.set_label(str(albumArt))

            super().keypress(size, key)


def main():
    # if len(sys.argv) <= 1:
    #     raise Warning("Provide a valid dir")
    # else:
    #     dir = sys.argv[1]
    dir="."
    message_q = Queue()
    state.stop_event = threading.Event()
    state.viewInfo = viewInfo.ViewInfo(dir)
    state.queueYt = message_q
    state.updateList = False
    display = Display()

    display.loop.run()

    for th in threading.enumerate():
        if th != threading.current_thread():
            th.join()


if __name__ == "__main__":
    main()
