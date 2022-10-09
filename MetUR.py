from __future__ import unicode_literals
import logging
import os
from queue import Queue
import queue
import sys
import eyed3
import urwid
from eyed3 import id3
import contextlib
from urwid import widget
from urwid.util import TagMarkupException
import musicPlayer
import spotifyInfo
import time
import tagModifier 
from youtube import Youtube 
import youtube
import threading
#Esta linea impide que se vean los errores de eyed3
logging.getLogger("eyed3.mp3.headers").setLevel(logging.CRITICAL)


class ViewInfo():
    def __init__(self,dir):
        self.dir=dir
        tagModifier.dir=dir
        os.chdir(dir)
        self.canciones=os.listdir(dir) 
        self.canciones=[x for x in self.canciones if "mp3" in x]
        self.canciones.sort()
    def getDir(self):
        return self.dir
    def addSong(self,song):
        self.canciones.append(song)
        self.canciones.sort()
    def deleteSong(self,song):
        self.canciones.remove(song)
        self.canciones.sort()
    def songInfo(self,index):
        if(len(self.canciones)==0):cancion=""
        else:cancion=self.canciones[index]
        return tagModifier.songInfo(cancion)
    def songFileName(self,index):
        if(len(self.canciones)>0):
            return self.canciones[index]
        return "None"
    def songsLen(self):
        return len(self.canciones)
    def isSong(self,filename):
        return filename in self.canciones
        

class Display():
    
    palette = [
    ('Title', 'black', 'light gray'),
    ('streak', 'black', 'dark red'),
    ('bg', 'black', 'dark blue'),
    ('reversed', 'standout', ''),]

    def __init__(self,viewInfo, msg_queue):
        """
        Constructor of display class which receives a viewInfo object.
        Here are initialized the widgets in a column layout composed of
        two piles, one for the list of songs and the other for the metadata editor
        and the youtubedl downloader.
        """
        self.viewInfo=viewInfo
        youtube.queueYt=msg_queue
        title,album,artist,albumArt=self.viewInfo.songInfo(0)
        pilaMetadata=[
            urwid.AttrMap(urwid.Text(str("File Name"),align="center"),"Title"),
            urwid.Text(self.viewInfo.songFileName(0),align="center"),
            urwid.AttrMap(urwid.Text(str("Title"),align="center"),"Title"),
            urwid.Edit(caption='', edit_text=str(title), multiline=False, align='center', wrap='space', allow_tab=False, edit_pos=None, layout=None, mask=None),
            urwid.AttrMap(urwid.Text(str("Album"),align="center"),"Title"),
            urwid.Edit(caption='', edit_text=str(album), multiline=False, align='center', wrap='space', allow_tab=False, edit_pos=None, layout=None, mask=None),
            urwid.AttrMap(urwid.Text(str("Artist"),align="center"),"Title"),
            urwid.Edit(caption='', edit_text=str(artist), multiline=False, align='center', wrap='space', allow_tab=False, edit_pos=None, layout=None, mask=None),
            urwid.AttrMap(urwid.Button(albumArt), None, focus_map='reversed'),
            urwid.AttrMap(urwid.Button("Ver Cover"), None, focus_map='reversed'),
            urwid.AttrMap(urwid.Button("Llenar Campos automaticamente"), None, focus_map='reversed'),
            urwid.AttrMap(urwid.Button("Llenar los campos de todas las canciones"), None, focus_map='reversed'),
            ]

        self.walker=urwid.SimpleListWalker(self.listMenu())
        self.lista=self.ListMod(self.walker,self)

        urwid.connect_signal(pilaMetadata[3],"change",self.editHandler) 
        urwid.connect_signal(pilaMetadata[5],"change",self.editHandler) 
        urwid.connect_signal(pilaMetadata[7],"change",self.editHandler) 
        urwid.connect_signal(pilaMetadata[8].original_widget,"click",self.setCover )
        urwid.connect_signal(pilaMetadata[9].original_widget,"click",self.verCover)
        urwid.connect_signal(pilaMetadata[10].original_widget,"click",self.llenarCampos)
        urwid.connect_signal(pilaMetadata[11].original_widget,"click",self.automatiCover)
       

        self.footer=urwid.AttrMap(urwid.Text("Cancion sonando: ninguna \n Para tocar Cancion preciona 'a' ",align="center"),"Title")
        self.pila=urwid.Pile(pilaMetadata)
        pilacomp=urwid.LineBox(urwid.Filler(self.pila, valign="top"),"Info")

        
        self.texto_info=urwid.Text("")
        self.youtube = Youtube(self.texto_info)
        editURL=self.CustomEdit("Escribe link: ", parent=self,multiline =True)
        textoDescarga=urwid.Filler(urwid.LineBox(editURL))
        texto_decorado=urwid.Filler(urwid.LineBox(self.texto_info,""))
        self.pilaYoutube=urwid.LineBox(urwid.Pile([textoDescarga,texto_decorado]),"Youtubedl")
        
        

        pila2=[pilacomp,self.pilaYoutube]
        self.pilaPrincipal=urwid.LineBox(urwid.Pile(pila2))
        self.columns=urwid.Columns([urwid.LineBox(self.lista,"Canciones"),self.pilaPrincipal],dividechars=4, focus_column=0, min_width=1, box_columns=None)
        self.frame=urwid.Frame(self.columns,footer=self.footer)
        self.loop=urwid.MainLoop(self.frame,self.palette,unhandled_input=self.exit,handle_mouse=False)
        self.msg_queue = msg_queue
        self.check_messages(self.loop, None)
       
    
    def check_messages(self, loop, *_args):
        """add message to bottom of screen"""
        loop.set_alarm_in(
            sec=0.5,
            callback=self.check_messages,
            )
        try:
            msg = self.msg_queue.get_nowait()
        except queue.Empty:
            return
        self.texto_info.set_text(msg)
        # self.updateWalker()
        # self.walker.append(
        #     urwid.Text(('body', msg))
        #     )
        # self.body.set_focus(
        #     len(self.walker)-1, 'above'
        #     )

    def exit(self,key):
        """
        functions that handles the exit of the application 
        """
        if key == "esc":
            raise urwid.ExitMainLoop()
            



    def changeFocus(self,button,text):
        """
        Small fuctions that is used by a button to change focus from the list to the metadata editor
        """
        if self.columns.focus_col==0:
            self.columns.focus_col=1

    def updateWalker(self):
        """
        Updates the walker in case a new song is added
        """
        canciones=os.listdir(self.viewInfo.getDir()) 
        canciones=[x for x in canciones if "mp3" in x]
        cancionesAgregar= list(set(canciones)-set(self.viewInfo.canciones))
        cancionesAgregar.sort()
        
        if(len(cancionesAgregar)>0):
            for cancion in cancionesAgregar:
                # cancion=max(os.listdir(),key=os.path.getctime)
                self.viewInfo.addSong(cancion)
                button = urwid.Button(cancion)
                urwid.connect_signal(button, 'click', self.changeFocus , cancion)
                self.walker.append(urwid.AttrMap(button, None, focus_map='reversed'))
                x=self.walker[-1].original_widget.get_label()
                self.walker.sort(key=lambda x : x.original_widget.get_label())
        else:
            for cancion in range(self.viewInfo.songsLen()):
                if(not self.viewInfo.songFileName(cancion) in canciones):
                    for widget in self.walker:
                        if(widget.original_widget.get_label()==self.viewInfo.songFileName(cancion)):
                            self.walker.remove(widget)
                            self.viewInfo.deleteSong(widget.original_widget.get_label())
                            break
                    break


    
            
    
    def update_text(self,read_data):
      
        self.texto_info.set_text(self.texto_info.text + read_data)   
        self.texto_info.set_text("kk")
            
    def listMenu(self):
        body=[]
        for i in range(self.viewInfo.songsLen()):
            cancion = self.viewInfo.songFileName(i)
            button = urwid.Button(cancion)
            urwid.connect_signal(button, 'click', self.changeFocus, cancion)
            body.append(urwid.AttrMap(button, None, focus_map='reversed'))
        return body
    
    def automatiCover(self,widget):
        for i in range(self.viewInfo.songsLen()):
            fileName=self.viewInfo.songFileName(i)
            tagModifier.llenarCampos(self.viewInfo.getDir(),fileName,show=False)       
            
    
        
          

    def editHandler(self,widget,text):
        if(os.path.isfile(self.viewInfo.songFileName(self.lista.focus_position))):
            audiofile=eyed3.load(self.viewInfo.songFileName(self.lista.focus_position))
        else:return
        indexWidget=-1

        for j,i in enumerate(self.pila.contents):
            if(i[0]==widget):
                indexWidget=j
                break

        textoInfo=self.pila.contents[indexWidget][0].get_edit_text()
        if indexWidget == 3:
            if(str(audiofile.tag.title)!=text):
                if(len(textoInfo)<=1):
                    tagModifier.changeTitle("",self.viewInfo.canciones[self.lista.focus_position])
                else:
                    tagModifier.changeTitle(textoInfo,self.viewInfo.canciones[self.lista.focus_position])
        elif indexWidget == 5:
            if(str(audiofile.tag.album)!=text):
                if(len(textoInfo)<=1):
                    tagModifier.changeAlbum("",self.viewInfo.canciones[self.lista.focus_position])
                else:
                    tagModifier.changeAlbum(textoInfo,self.viewInfo.canciones[self.lista.focus_position])
                
        elif indexWidget == 7:
            if(str(audiofile.tag.artist)!=text):
                if(len(textoInfo)<=1):
                    tagModifier.changeArtist("",self.viewInfo.canciones[self.lista.focus_position])
                else:
                    tagModifier.changeArtist(textoInfo,self.viewInfo.canciones[self.lista.focus_position])
                
    
    def llenarCampos(self,widget=None,fileName=None):

        if(fileName==None):fileName=self.viewInfo.songFileName(self.lista.focus_position)
        tagModifier.llenarCampos(self.viewInfo.getDir(),fileName)
        title,album,artist,albumArt=self.viewInfo.songInfo(self.lista.focus_position)
        os.chdir(self.viewInfo.getDir())
        self.pila.contents[1][0].set_text(str(fileName))
        self.pila.contents[3][0].set_edit_text(str(title))
        self.pila.contents[5][0].set_edit_text(str(album))
        self.pila.contents[7][0].set_edit_text(str(artist))   
        self.pila.contents[8][0].original_widget.set_label(str(albumArt))
        if(title is None or title!="None"):
            self.pila.contents[-2][0].original_widget.set_label("No se encontro la informacion")
    

    def verCover(self,widget=None):

        fileName=self.viewInfo.canciones[self.lista.focus_position]
        tagModifier.verCover(fileName)


    def setCover(self,wid=None,fileName=None):
        if(fileName==None):fileName=self.viewInfo.canciones[self.lista.focus_position]
        audiofile=eyed3.load(self.viewInfo.canciones[self.lista.focus_position])
        if len(audiofile.tag.images)==0:

            tagModifier.setCover(self.viewInfo.getDir(),fileName)
            audiofile=eyed3.load(self.viewInfo.canciones[self.lista.focus_position])
            if wid != None:
                if len(audiofile.tag.images)==0:
                    wid.set_label("Cover no encontrada")
                else:
                    wid.set_label("Cover asignada")
               
        else:
            tagModifier.removeAlbumCover(fileName)
            if wid!=None: 
                wid.set_label("Cover eliminada")

    class CustomEdit(urwid.Edit):
        """
        Custom edit widget create for the youtubedl url widget that deletes the text 
        after the dowload is done 
        """
        def __init__(self, caption=u"", edit_text=u"", multiline=False, parent=None):
            super().__init__(caption, edit_text, multiline)
            self.parent=parent
        
        def URLDownload(self, text): 
        
            threading.Thread(
            target=self.parent.youtube.youtube_descarga, args=[text],
            name='update_time',
            ).start()
            
                # self.parent.youtube.youtube_descarga(text)
            super().set_edit_text('')
              
        def set_edit_text(self, text):
            if text.endswith('\n'):
                self.URLDownload(text)
                self.parent.updateWalker()
                
            else:
                super().set_edit_text(text)
           
    class ListMod(urwid.ListBox):
        """
        Custom listbox widget that handles key inputs to move through 
        the songs and to display them in the right panel.
        """

        def __init__(self, body,display):
            self.display=display
            super().__init__(body)

        # def render(self, size, focus ):
        #     # self.display.updateWalker()
        #     super().render(size,False)

        def keypress(self, size, key): 
            
            cursorPos=self.get_focus()[1]
           

            self.display.pila.contents[-2][0].original_widget.set_label("Llenar Campos automaticamente")
            
            if key == 'down':
                if(self.focus!=None):
                    cursorPos=cursorPos+1
                    if(cursorPos>=len(self.body)):cursorPos-=1
            elif key == 'up':
                if(self.focus!=None):
                    cursorPos=cursorPos-1
                    if(cursorPos<0):cursorPos=0
            elif key == 'right':
                if self.display.columns.focus_col==0:
                    self.display.columns.focus_col=1
            elif key == "esc":
                self.display.exit(key)
            elif key == "delete":
                os.remove(self.display.viewInfo.songFileName(cursorPos))
                self.display.updateWalker()
                cursorPos=self.get_focus()[1]
                # if(cursorPos>len(self.body)):cursorPos-=1
                title,album,artist,albumArt=self.display.viewInfo.songInfo(cursorPos)
               
                os.chdir(self.display.viewInfo.dir)
                self.display.pila.contents[1][0].set_text(str(self.display.viewInfo.songFileName(cursorPos)))
                self.display.pila.contents[3][0].set_edit_text(str(title))
                self.display.pila.contents[5][0].set_edit_text(str(album))
                self.display.pila.contents[7][0].set_edit_text(str(artist))   
                self.display.pila.contents[8][0].original_widget.set_label(str(albumArt)) 
            elif key == 's':
                if(self.focus!=None):
                    musicPlayer.resume_pause(self.display.viewInfo.songFileName(cursorPos))
            elif key == 'a':
                if(self.focus!=None):
                    musicPlayer.setMedia(self.display.viewInfo.songFileName(cursorPos))
                    self.display.footer.original_widget.set_text("Cancion sonando:"+ self.display.viewInfo.songFileName(cursorPos)+ "\n Para tocar Cancion presiona a y para pausar presiona s ")
             
            if(cursorPos is None):
                super().keypress(size, key)
                return

            if (key in {'down','up'} and  cursorPos<len(self.body)):
                
                title,album,artist,albumArt=self.display.viewInfo.songInfo(cursorPos)
                os.chdir(self.display.viewInfo.dir)
                self.display.pila.contents[1][0].set_text(str(self.display.viewInfo.songFileName(cursorPos)))
                self.display.pila.contents[3][0].set_edit_text(str(title))
                self.display.pila.contents[5][0].set_edit_text(str(album))
                self.display.pila.contents[7][0].set_edit_text(str(artist))   
                self.display.pila.contents[8][0].original_widget.set_label(str(albumArt))                                                           
                
            super().keypress(size, key)

def update_time(stop_event, msg_queue):
    """send timestamp to queue every second"""
    logging.info('start')
    while not stop_event.wait(timeout=1.0):
        msg_queue.put( time.strftime('time %X') )
    logging.info('stop')
    
def main():
    if(len(sys.argv)<=1):
            print("Ingrese un directorio valido")
            dir=input()
    else: dir=sys.argv[1]
    
    stop_ev = threading.Event()
    message_q = queue.Queue()

    # threading.Thread(
    #     target=update_time, args=[stop_ev, message_q],
    #     name='update_time',
    # ).start()
    Display( ViewInfo(dir), message_q).loop.run()
    stop_ev.set()
    for th in threading.enumerate():
        if th != threading.current_thread():
            th.join()

if __name__=="__main__":
    main()
    