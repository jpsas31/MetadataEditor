import yt_dlp

from src.singleton import BorgSingleton

state = BorgSingleton()


class Youtube:
    class MyLogger:
        def debug(self, msg):
            state.queueYt.put(msg)

        def warning(self, msg):
            state.queueYt.put(msg)

        def error(self, msg):
            state.queueYt.put(msg)

    def endHook(self, d):
        if d["status"] == "finished":
            state.queueYt.put("Download is Done")

    def youtube_descarga(self, link):
        download_options = {
            "format": "bestaudio/best",
            "no_warnings": True,
            "ignoreerrors": True,
            "logger": self.MyLogger(),
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
                state.updateList = True
                ydl.download([link])
                state.updateList = False
                state.queueYt.put("Done")
            except yt_dlp.utils.DownloadError as error:
                state.updateList = False
                raise yt_dlp.utils.DownloadError(
                    f"Unable to download video with error: {error}"
                )
