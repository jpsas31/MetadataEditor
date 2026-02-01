import logging
from queue import Queue

import yt_dlp

logging.basicConfig(
    filename="/tmp/album_art_debug.log",
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filemode="w",
)
logger = logging.getLogger(__name__)


class YoutubeLogger:
    def __init__(self, message_queue):
        logger.info(f"YoutubeLogger initialized with message_queue: {message_queue}")
        self.message_queue = message_queue

    def debug(self, msg):
        logger.info(f"YoutubeLogger debug: {msg}")
        self.message_queue.put(msg)

    def warning(self, msg):
        logger.info(f"YoutubeLogger warning: {msg}")
        self.message_queue.put(msg)

    def error(self, msg):
        logger.info(f"YoutubeLogger error: {msg}")
        self.message_queue.put(msg)


class Youtube:
    def __init__(self, parent):
        self.parent = parent
        self.message_queue = Queue()
        logger.info(f"Youtube initialized with parent: {self.parent}")

    def end_hook(self, d):
        if d["status"] == "finished":
            self.message_queue.put("Download is Done")
            logger.info("Download is Done")

    def youtube_descarga(self, link):
        logger.info(f"Downloading URL: {link}")
        download_options = {
            "format": "bestaudio/best",
            "no_warnings": True,
            "ignoreerrors": True,
            "logger": YoutubeLogger(self.message_queue),
            "outtmpl": "%(title)s.%(ext)s",
            "nocheckcertificate": True,
            "progress_hooks": [self.end_hook],
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }
            ],
        }
        logger.info(f"Download options: {download_options}")
        with yt_dlp.YoutubeDL(download_options) as ydl:
            ydl.cache.remove()
            try:
                self.parent.should_update_song_list = True
                logger.info(f"Downloading URL: {link}")
                ydl.download([link])
                logger.info("Download is Done")
                self.parent.should_update_song_list = False
                self.message_queue.put("Done")
                logger.info("Done")
            except yt_dlp.utils.DownloadError as error:
                self.parent.should_update_song_list = False
                logger.info(f"Unable to download video with error: {error}")
                raise yt_dlp.utils.DownloadError(f"Unable to download video with error: {error}")
