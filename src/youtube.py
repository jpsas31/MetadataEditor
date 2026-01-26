from queue import Queue

import yt_dlp


class YoutubeLogger:
    def __init__(self, message_queue):
        self.message_queue = message_queue

    def debug(self, msg):
        self.message_queue.put(msg)

    def warning(self, msg):
        self.message_queue.put(msg)

    def error(self, msg):
        self.message_queue.put(msg)


class Youtube:
    def __init__(self):
        self.message_queue = Queue()
        self.update_list = False

    def end_hook(self, d):
        if d["status"] == "finished":
            self.message_queue.put("Download is Done")

    def youtube_descarga(self, link):
        download_options = {
            "format": "bestaudio/best",
            "no_warnings": True,
            "ignoreerrors": True,
            "logger": YoutubeLogger(self.message_queue),
            "outtmpl": "%(title)s.%(ext)s",
            "nocheckcertificate": True,
            "progress_hooks": [self.endHook],
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }
            ],
        }

        with yt_dlp.YoutubeDL(download_options) as ydl:
            ydl.cache.remove()
            try:
                self.update_list = True
                ydl.download([link])
                self.update_list = False
                self.message_queue.put("Done")
            except yt_dlp.utils.DownloadError as error:
                self.update_list = False
                raise yt_dlp.utils.DownloadError(f"Unable to download video with error: {error}")
