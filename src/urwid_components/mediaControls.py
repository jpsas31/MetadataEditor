from datetime import timedelta

import urwid

from src.singleton import BorgSingleton

state = BorgSingleton()


class MediaProgressBar(urwid.ProgressBar):
    def __init__(self, normal, complete, current=0, done=100, satt=None):
        super().__init__(normal, complete, current, done, satt)

    def set_done(self, done):
        self.done = max(done, 1)

    def get_text(self):
        time_string = str(timedelta(milliseconds=int(self.current)))
        if time_string.find(".") != -1:
            time_string = time_string[: time_string.find(".")]
        return (
            time_string[time_string.find(":") + 1 :]
            if time_string[0] == "0"
            else time_string
        )

    def update_position(self, sound_length, play_position):
        self.set_done(sound_length)
        self.set_completion(play_position)
        if play_position >= sound_length:
            self.set_done(0)
            self.set_completion(0)
