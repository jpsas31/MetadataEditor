import queue
import threading
from io import BytesIO

import urwid
from climage import convert, convert_pil
from mutagen.id3 import APIC, ID3, TALB, TIT2, TPE1
from PIL import Image, ImageFile

from src.urwid_components.ansiWidget import ANSIWidget
from src.urwid_components.display import Display


class MainLoopManager:
    def __init__(self, state):
        self.display = Display(self.change_view)
        self.state = state
        apic_frame =  ID3("/Users/jpsalgado@truora.com/MetadataEditor/testMusic/Aerophon - Salvavidas Feat Juan Pablo Vega  (Horizonte 2018).mp3").get("APIC:Cover")
        if apic_frame:
            img = Image.open(BytesIO(apic_frame.data))
            ImageFile.LOAD_TRUNCATED_IMAGES = True

        body = ANSIWidget(convert_pil(img, is_unicode=True, width=60))
        body = urwid.Pile([body])

        self.views = [
            self.display.frame,
            body,
        ]

        initial_view = self.views[0]
        self.loop = urwid.MainLoop(
            initial_view, palette=self.display.palette, unhandled_input=self.exit
        )

        threading.Thread(
            target=self.display.audio_player.thread_play,
            args=[self.display.footer.music_bar.update_position],
        ).start()

        self._schedule_message_check()

    def _schedule_message_check(self):
        self.loop.set_alarm_in(0.5, self._check_messages)

    def _check_messages(self, loop, *_args):
        if self.state.updateList:
            loop.set_alarm_in(5, self.display._update_song_list)

        try:
            msg = self.state.queueYt.get_nowait()
            self.display.text_info.set_text(msg)
        except queue.Empty:
            pass

        self._schedule_message_check()

    def change_view(self, index):
        self.loop.widget = self.views[index]

    def exit(self, key):
        if key == "esc":
            self.state.stop_event.set()
            raise urwid.ExitMainLoop()
        elif key in "123":
            try:
                self.change_view(int(key) - 1)
            except StopIteration:
                raise urwid.ExitMainLoop()

    def start(self):
        self.loop.run()
