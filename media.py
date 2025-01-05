from os import environ
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
import pygame.mixer
from singleton import BorgSingleton

class AudioPlayer:
    def __init__(self):
        self.state = BorgSingleton()
        self.paused = False
        self.current_sound = None
        self.sound_length = 0
        self.play_position = 0
        pygame.mixer.init()

    def set_media(self, file_name):
        if not pygame.mixer.get_init():
            pygame.mixer.init()

        pygame.mixer.music.load(file_name)
        self.current_sound = pygame.mixer.music
        self.sound_length = pygame.mixer.Sound(file_name).get_length() * 1000
        self.play_position = 0
        self.current_sound.play()

    def resume_pause(self):
        if self.current_sound is None:
            return 
        
        if self.current_sound.get_busy():
            self.play_position = pygame.mixer.music.get_pos()
            self.current_sound.pause()
        else:
            self.current_sound.unpause()

    def get_play_position(self):
        
        return pygame.mixer.music.get_pos()

    def is_playing(self):
        if self.current_sound is None:
            return False
        
        return self.current_sound.get_busy()

    def stop(self):
        pygame.mixer.music.stop()

    
    def thread_play(self, update_position):
        while not self.state.stop_event.is_set():
            if self.is_playing():
                update_position(self.sound_length, self.get_play_position())
        pygame.mixer.quit()   