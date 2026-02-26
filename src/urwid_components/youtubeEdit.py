import threading

import urwid

from src.logging_config import setup_logging

logger = setup_logging(__name__)


class CustomEdit(urwid.Edit):
    def __init__(self, caption="", edit_text="", multiline=False, parent=None, youtube=None):
        super().__init__(caption, edit_text, multiline)
        self.parent = parent
        self.youtube = youtube
        self.read_only = False
        logger.info(
            f"CustomEdit initialized with parent: {self.parent} and youtube: {self.youtube}"
        )

    def keypress(
        self,
        size: tuple[int],
        key: str,
    ):
        if self.read_only and key not in ("up", "down", "left", "right", "esc"):
            return None

        return super().keypress(size, key)

    def set_edit_text(self, text):
        logger.info(f"Setting edit text to: {text}")
        if text.endswith("\n"):
            logger.info(f"Downloading URL: {text.strip()}")
            self.toggle_read_only_text()
            self._download_url(text.strip())
            logger.info("Updating song list")
            self.parent._update_song_list()
            logger.info("Song list updated")
            self.toggle_read_only_text()
        else:
            super().set_edit_text(text)
            logger.info(f"Edit text set to: {text}")

    def toggle_read_only_text(self):
        if self.read_only:
            self.read_only = False
            return

        self.read_only = True

    def download_url(self, text):
        self.toggle_read_only_text()
        self.youtube.youtube_descarga(text)
        self.toggle_read_only_text()

    def _download_url(self, text):
        threading.Thread(target=self.download_url, args=[text], name="ydl_download").start()
