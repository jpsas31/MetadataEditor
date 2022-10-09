from youtube_dl import YoutubeDL


class MyLogger(object):
    def debug(self, msg):
        # print('debug information: %r' % msg)
        pass

    def warning(self, msg):
        # print('warning: %r' % msg)
        pass

    def error(self, msg):
        # print('error: %r' % msg)
        pass


options = {
    "restrictfilenames": True,
    "progress_with_newline": True,
    "logger": MyLogger(),
}

url = 'http://www.youtube.com/watch?v=BaW_jenozKc'
with YoutubeDL(options) as ydl:
    ydl.download([url])

