from datetime import timedelta
import urwid
import vlc
from singleton import BorgSingleton
state=BorgSingleton()
Instance = vlc.Instance()
player = Instance.media_player_new()
paused=False
duration = player.get_length()

def setMedia(fileName):
    Media = Instance.media_new(fileName)
    player.set_media(Media)
    player.play()
    

def resume_pause():
    global paused
    if not paused:
        player.set_pause(1)
        
    else:
        player.set_pause(0)
        
    paused = not paused
    
class MediaProgressBar(urwid.ProgressBar):
    def __init__(self, normal, complete, current=0, done=100, satt=None):
        super().__init__(normal, complete, current, done, satt)
       
        
    def setDone(self,done):
        
        if done == 0: 
            done = 1
        self.done=done
        
    def get_text(self):
        timeString = str(timedelta(milliseconds=int(self.current)))
        if timeString[0] == '0':
            return timeString[timeString.find(':')+1:]
        return timeString
        
 
    def threadPlay(self):       
        while not state.stop_event.wait(timeout=1.0):
            while not player.is_playing():
                self.setDone(player.get_length())
                
            self.set_completion((player.get_time()))
            if not player.is_playing():
                self.setDone(0)
                self.set_completion((0))
                
class Footer(urwid.Pile):
    def __init__(self) -> None:
        self.musicBar = MediaProgressBar("normal", "complete")
        super().__init__([
                urwid.AttrMap(
                    urwid.Text(
                        "",
                        align="center",
                    ),
                    "Title",
                ),
                self.musicBar,
            ])

