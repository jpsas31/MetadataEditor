from cgitb import text
from warnings import catch_warnings
import youtube_dl
import urwid
from queue import Queue
from threading import Thread

queueYt=0

class Youtube():
    def __init__(self, textWidg):
       
        self.textWidget=textWidg
     
          
        
    class MyLogger(object):
     
        def debug(self, msg):
            # print(msg)
            # pass
            queueYt.put(msg)
            # self.textWidg.set_text(f'{msg}')

        def warning(self, msg):
            # print(msg)
            # pass
            queueYt.put(msg)
            # self.textWidg.set_text(f'{msg}')

        def error(self, msg):
            # print(msg)
            # pass
            queueYt.put(msg)
            # self.textWidg.set_text(f'{msg}')

    def endHook(self,d):
        if d['status'] == 'finished':
            queueYt.put('Download is Done')

    def youtube_descarga(self,link):
  
    #    https://www.youtube.com/watch?v=9sPthPleEKo
        download_options={
            'format': 'bestaudio/best',
            # 'quite': True,
            'no_warnings': True,
            'logger': self.MyLogger(),
            'outtmpl': '%(title)s.%(ext)s',
            'nocheckcertificate': True,
            'progress_hooks': [self.endHook],
            'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                                                        
                                }],
                            
                }
        
        with youtube_dl.YoutubeDL(download_options) as ydl:
            ydl.cache.remove()
            try:
                ydl.download([link])
                queueYt.put('Done')
            except:pass
        

