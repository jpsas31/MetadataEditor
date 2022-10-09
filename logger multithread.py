from queue import Queue
from threading import Thread
from youtube_dl import YoutubeDL

q = Queue()
class MyLogger(object):
    def debug(self, msg):
        # print('debug information: %r' % msg)
        q.put(msg)
        pass

    def warning(self, msg):
        q.put(msg)
        # print('warning: %r' % msg)
        pass

    def error(self, msg):
        q.put(msg)
        # print('error: %r' % msg)
        pass


def producer(out_q):
    url = 'http://www.youtube.com/watch?v=BaW_jenozKc'
    options = {
    "restrictfilenames": True,
    "progress_with_newline": True,
    "logger": MyLogger(),
    }


    with YoutubeDL(options) as ydl:
        ydl.download([url])
    
          
# A thread that consumes data
def consumer(in_q):
    while True:
        # Get some data
        data = in_q.get()
        print(data)
        # Process the data
        ...
          
# Create the shared queue and launch both threads

t1 = Thread(target = consumer, args =(q, ))
t2 = Thread(target = producer, args =(q, ))
t1.start()
t2.start()