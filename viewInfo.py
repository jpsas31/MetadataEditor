import tagModifier
import os
class ViewInfo:
    
    def __init__(self, dir):
        self.dir = dir
        tagModifier.dir = dir
        os.chdir(dir)
        self.canciones = os.listdir(dir)
        self.canciones = [x for x in self.canciones if "mp3" in x]
        self.canciones.sort()

    def getDir(self):
        return self.dir

    def addSong(self, song):
        self.canciones.append(song)
        self.canciones.sort()

    def deleteSong(self, song):
        self.canciones.remove(song)
        self.canciones.sort()

    def songInfo(self, index):
        if len(self.canciones) == 0:
            cancion = ""
        else:
            cancion = self.canciones[index]
        return tagModifier.MP3Editor(cancion).song_info()

    def songFileName(self, index):
        if len(self.canciones) > 0:
            return self.canciones[index]
        return "None"

    def songsLen(self):
        return len(self.canciones)

    def isSong(self, filename):
        return filename in self.canciones