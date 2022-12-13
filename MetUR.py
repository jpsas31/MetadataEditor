import logging
import os
import sys
import threading
from queue import Queue
import queue
import urwid
import media
import metadataEditorPop
import viewInfo
import popupMenu
from youtube import Youtube
from singleton import BorgSingleton
# Esta linea impide que se vean los errores de eyed3
logging.getLogger("eyed3.mp3.headers").setLevel(logging.CRITICAL)

state=BorgSingleton()
class Display:

    palette = [
        ("Title", 'black', 'light blue'),
        ("streak", "black", "dark red"),
        ("bg", "black", "dark blue"),
        ("reversed", "standout", ""),
        ('normal', 'black', 'light blue'),
        ('complete', 'black', 'dark magenta')
    ]

    def __init__(self):
        """
        Constructor of display class which receives a viewInfo object.
        Here are initialized the widgets in a column layout composed of
        two piles, one for the list of songs and the other for the metadata editor
        and the youtubedl downloader.
        """
       
        title, album, artist, albumArt = state.viewInfo.songInfo(0)
        self.walker = urwid.SimpleListWalker(self.listMenu())
        self.lista = self.ListMod(self.walker, self)
        self.pilaMetadata = metadataEditorPop.MetadaEditor(self.lista,'pilaMetadata')

        state.pilaMetadata = self.pilaMetadata

       

        self.footer = media.Footer()
        self.pila = self.pilaMetadata
        # pilacomp = urwid.LineBox(urwid.Filler(self.pila, valign="top"), "Info")
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
        
        threading.Thread(target=self.footer.musicBar.threadPlay, args=[]).start()
        self.check_messages(self.loop, None)

    def check_messages(self, loop, *_args):
        """add message to bottom of screen"""
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
        """
        functions that handles the exit of the application
        """
        if key == "esc":
            raise urwid.ExitMainLoop()

    def changeFocus(self, button, text):
        """
        Small fuctions that is used by a button to change focus from the list to the metadata editor
        """
        if self.columns.focus_col == 0:
            self.columns.focus_col = 1

    def updateWalker(self,a=None,b=None):
        """
        Updates the walker in case a new song is added
        """
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
                x = self.walker[-1].original_widget.get_label()
                self.walker.sort(key=lambda x: x.original_widget.get_label())
        else:
            for cancion in range(state.viewInfo.songsLen()):
                if not state.viewInfo.songFileName(cancion) in canciones:
                    for widget in self.walker:
                        if (
                            widget.original_widget.get_label()
                            == state.viewInfo.songFileName(cancion)
                        ):
                            self.walker.remove(widget)
                            state.viewInfo.deleteSong(widget.original_widget.get_label())
                            break
                    break


    def listMenu(self):
        body = []
        for i in range(state.viewInfo.songsLen()):
            cancion = state.viewInfo.songFileName(i)
            button = urwid.Button(cancion)
            urwid.connect_signal(button, "click", self.changeFocus, cancion)
            body.append(urwid.AttrMap(button, None, focus_map="reversed"))
        return body

    class CustomEdit(urwid.Edit):
        """
        Custom edit widget create for the youtubedl url widget that deletes the text
        after the dowload is done
        """

        def __init__(self, caption="", edit_text="", multiline=False, parent=None):
            super().__init__(caption, edit_text, multiline)
            self.parent = parent
            self.youtube= Youtube()

        def URLDownload(self, text):

            threading.Thread(
                target=self.youtube.youtube_descarga,
                args=[text],
                name="ydl_download",
            ).start()

            super().set_edit_text("")

        def set_edit_text(self, text):
            if text.endswith("\n"):
                self.URLDownload(text)
                self.parent.updateWalker()

            else:
                super().set_edit_text(text)

    class ListMod(urwid.ListBox):
        """
        Custom listbox widget that handles key inputs to move through
        the songs and to display them in the right panel.
        """

        def __init__(self, body, display):
            self.display = display
            super().__init__(body)


        def keypress(self, size, key):

            cursorPos = self.get_focus()[1]

            self.display.pila.contents[-3].original_widget.set_label(
                "Llenar Campos automaticamente"
            )

            if key == "down":
                if self.focus != None:
                    cursorPos = cursorPos + 1
                    if cursorPos >= len(self.body):
                        cursorPos -= 1
            elif key == "up":
                if self.focus != None:
                    cursorPos = cursorPos - 1
                    if cursorPos < 0:
                        cursorPos = 0
            elif key == "right":
                if self.display.columns.focus_col == 0:
                    self.display.columns.focus_col = 1
            elif key == "esc":
                self.display.exit(key)
            elif key == "delete":
                os.remove(state.viewInfo.songFileName(cursorPos))
                self.display.updateWalker()
                cursorPos = self.get_focus()[1]
                # if(cursorPos>len(self.body)):cursorPos-=1
                title, album, artist, albumArt = state.viewInfo.songInfo(
                    cursorPos
                )

                os.chdir(state.viewInfo.dir)
                self.display.pila.contents[1].set_text(
                    str(state.viewInfo.songFileName(cursorPos))
                )
                self.display.pila.contents[3].set_edit_text(str(title))
                self.display.pila.contents[5].set_edit_text(str(album))
                self.display.pila.contents[7].set_edit_text(str(artist))
                self.display.pila.contents[8].original_widget.set_label(
                    str(albumArt)
                )
            elif key == "s":
                if self.focus != None:
                    media.resume_pause()
            elif key == "a":
                if self.focus != None:
                    media.setMedia(state.viewInfo.songFileName(cursorPos))
                    self.display.footer[0].set_text(
                        state.viewInfo.songFileName(cursorPos)
                    )

            if cursorPos is None:
                super().keypress(size, key)
                return

            if key in {"down", "up"} and cursorPos < len(self.body):

                title, album, artist, albumArt = state.viewInfo.songInfo(
                    cursorPos
                )
                os.chdir(state.viewInfo.dir)
                self.display.pila.contents[1].set_text(
                    str(state.viewInfo.songFileName(cursorPos))
                )
                self.display.pila.contents[3].set_edit_text(str(title))
                self.display.pila.contents[5].set_edit_text(str(album))
                self.display.pila.contents[7].set_edit_text(str(artist))
                self.display.pila.contents[8].original_widget.set_label(
                    str(albumArt)
                )

            super().keypress(size, key)


def main():
    if len(sys.argv) <= 1:
        print("Ingrese un directorio valido")
        dir = input()
    else:
        dir = sys.argv[1]

    stop_ev = threading.Event()
    message_q = Queue()
    state.stop_event=stop_ev
    state.viewInfo=viewInfo.ViewInfo(dir)
    state.queueYt=message_q
    state.updateList=False
    display=Display()
    
    display.loop.run()
    
    stop_ev.set()
    for th in threading.enumerate():
        if th != threading.current_thread():
            th.join()


if __name__ == "__main__":
    main()
