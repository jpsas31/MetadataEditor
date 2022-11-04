import logging
import queue
import sys
import threading
import time

import urwid
import vlc

from media import MediaProgressBar

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)-4s %(threadName)s %(message)s", 
    datefmt="%H:%M:%S",
    filename='trace.log',
)

class Interface:
    palette = [
        ('body', 'white', 'black'),
        ('ext', 'white', 'dark blue'),
        ('ext_hi', 'light cyan', 'dark blue', 'bold'),
        ('normal', 'black', 'light gray'),
        ('complete', 'black', 'dark red')
        ]

    header_text = [
        ('ext_hi', 'ESC'), ':quit        ',
        ('ext_hi', 'UP'), ',', ('ext_hi', 'DOWN'), ':scroll',
        ]

    def __init__(self, msg_queue):
        self.header = urwid.AttrWrap(urwid.Text(self.header_text), 'ext')
        self.flowWalker = urwid.SimpleListWalker([])
        self.body = urwid.ListBox(self.flowWalker)
        self.bar = MediaProgressBar('normal','complete')
        self.bar.setDone(1218264)
        self.footer = urwid.AttrWrap(self.bar, 'ext')
        self.view = urwid.Frame(
            urwid.AttrWrap(self.body, 'body'),
            header = self.header,
            footer = self.footer)
        self.loop = urwid.MainLoop(self.view, self.palette, 
            unhandled_input = self.unhandled_input)
        self.msg_queue = msg_queue
        self.check_messages(self.loop, None)
        self.changeBar(self.loop,None)

    def unhandled_input(self, k):
        if k == 'esc':
            raise urwid.ExitMainLoop()

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
        if(isinstance(msg,int)):
            self.msg_queue.put(msg)
            return
        self.flowWalker.append(
            urwid.Text(('body', msg))
            )
        self.body.set_focus(
            len(self.flowWalker)-1, 'above'
            )
        
    def changeBar(self,loop,*_args):
        loop.set_alarm_in(
            sec=0.00001,
            callback=self.changeBar,
            )
        try:
            msg = self.msg_queue.get_nowait()
        except queue.Empty:
            return
        if(not isinstance(msg,int)):
            self.msg_queue.put(msg)
            return
        self.bar.set_completion(msg)
        # loop.draw_screen()
        # self.changeBar(loop,None)

def update_time(stop_event, msg_queue):
    """send timestamp to queue every second"""
    logging.info('start')
    while not stop_event.wait(timeout=1.0):
        msg_queue.put( time.strftime('time %X') )
    logging.info('stop')
    
def update_song(stop_event, msg_queue):
    inst = vlc.Instance() # Create a VLC instance
    media=inst.media_new('/home/pablo/Codigo/python/musica/ASMR The Deepest Tingles.mp3')
    play = inst.media_player_new() # Create a player instance
    play.set_media(media)
    media.parse()
    play.play()
    time.sleep(0.1)
    duration = play.get_length()
    # p.setDone(duration)
    while not stop_event.wait(timeout=0.002):
        # time.sleep(0.02)
        msg_queue.put( int(play.get_time()))

        if not play.is_playing():
            break
   

if __name__ == '__main__':

    stop_ev = threading.Event()
    message_q = queue.Queue()

    threading.Thread(
        target=update_time, args=[stop_ev, message_q],
        name='update_time',
    ).start()
    threading.Thread(
        target=update_song, args=[stop_ev, message_q],
        name='update_song',
    ).start()

    logging.info('start')
    Interface(message_q).loop.run()
    logging.info('stop')

    # after interface exits, signal threads to exit, wait for them
    logging.info('stopping threads')

    stop_ev.set()
    for th in threading.enumerate():
        if th != threading.current_thread():
            th.join()
