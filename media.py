import pygame.mixer
from datetime import timedelta
import urwid
from threading import Event
from singleton import BorgSingleton


state = BorgSingleton()
state.stop_event = Event()
paused = False
current_sound = None
sound_length = 0
play_position = 0 


pygame.mixer.init()

def setMedia(fileName):
    """
    Load a new sound file and play it.
    """
    global current_sound, sound_length, play_position

    if not pygame.mixer.get_init():
        pygame.mixer.init()

    pygame.mixer.music.load(fileName)
    current_sound =pygame.mixer.music
    sound_length = pygame.mixer.Sound(fileName).get_length() * 1000
    play_position = 0 
    current_sound.play()

def resume_pause():  
    global play_position
    if current_sound.get_busy():
        play_position = pygame.mixer.music.get_pos()
        current_sound.pause()
    else:
        current_sound.unpause()


class MediaProgressBar(urwid.ProgressBar):
    def __init__(self, normal, complete, current=0, done=100, satt=None):
        super().__init__(normal, complete, current, done, satt)

    def setDone(self, done):
        """
        Set the progress bar's total duration.
        """
        if done == 0:
            done = 1
        self.done = done

    def get_text(self):
        """
        Return the progress time in MM:SS format.
        """
        timeString = str(timedelta(milliseconds=int(self.current)))
        if timeString[0] == '0':
            return timeString[timeString.find(':') + 1:]
        return timeString

    def threadPlay(self):
        """
        Continuously update the progress bar while playing.
        """
        global play_position
        while not state.stop_event.wait(timeout=1.0):
            if current_sound:
                self.setDone(sound_length)
                play_position = pygame.mixer.music.get_pos()
                self.set_completion(play_position)
                if play_position >= sound_length:
                    # Reset if playback ends
                    self.setDone(0)
                    self.set_completion(0)

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
