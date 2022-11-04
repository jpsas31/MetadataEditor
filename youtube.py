import youtube_dl
from singleton import BorgSingleton


state=BorgSingleton()
class Youtube():        
    class MyLogger(object):
     
        def debug(self, msg):
            state.queueYt.put(msg)

        def warning(self, msg):
            state.queueYt.put(msg)

        def error(self, msg):
            state.queueYt.put(msg)

    def endHook(self,d):
        if d['status'] == 'finished':
            state.queueYt.put('Download is Done')

    def youtube_descarga(self,link):
        download_options={
            'format': 'bestaudio/best',
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
                state.updateList=True
                ydl.download([link])
                state.updateList=False
                state.queueYt.put('Done')
            except:
                state.updateList=False

