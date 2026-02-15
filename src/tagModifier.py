from io import BytesIO

import requests
from mutagen.id3 import APIC, ID3, TALB, TIT2, TPE1
from PIL import Image

import src.trackInfo as trackInfo


class MP3Editor:
    def __init__(self, file_path):
        self.file_path = file_path
        self.audiofile = ID3(file_path)

    def change_artist(self, text, save=True):
        """Change artist tag. Set save=False to batch multiple changes."""
        self.audiofile.add(TPE1(encoding=3, text=text))
        if save:
            self.audiofile.save()

    def change_title(self, text, save=True):
        """Change title tag. Set save=False to batch multiple changes."""
        self.audiofile.add(TIT2(encoding=3, text=text))
        if save:
            self.audiofile.save()

    def change_album(self, text, save=True):
        """Change album tag. Set save=False to batch multiple changes."""
        self.audiofile.add(TALB(encoding=3, text=text))
        if save:
            self.audiofile.save()

    def save(self):
        """Explicitly save all pending changes to the file."""
        self.audiofile.save()

    def add_album_cover(self, image_link, show=False):
        try:
            resp = requests.get(image_link, stream=True, timeout=10)
            resp.raise_for_status()

            image_data = resp.content

            if not self.audiofile.get("APIC:Cover"):
                self.audiofile.add(
                    APIC(
                        encoding=3,
                        mime="image/jpeg",
                        type=3,
                        desc="Cover",
                        data=image_data,
                    )
                )
                self.audiofile.save()
        except requests.RequestException as e:
            print(f"Error downloading album cover: {e}")
        except Exception as e:
            print(f"Error adding album cover: {e}")

    def show_album_cover(self):
        """Show album cover - disabled to prevent external viewer popup."""

        pass

    def get_cover(self):
        apic_frame = self.audiofile.get("APIC:Cover")
        if apic_frame:
            return Image.open(BytesIO(apic_frame.data))
        return None

    def remove_album_cover(self):
        self.audiofile.delall("APIC:Cover")
        self.audiofile.save()

    def song_info(self):
        title = self.audiofile.get("TIT2").text[0] if self.audiofile.get("TIT2") else ""
        album = self.audiofile.get("TALB").text[0] if self.audiofile.get("TALB") else ""
        artist = self.audiofile.get("TPE1").text[0] if self.audiofile.get("TPE1") else ""
        album_art = False if self.audiofile.get("APIC:Cover") == "" else True
        album_art = "Has cover" if album_art else "No Cover"
        return title, album, artist, album_art

    def has_metadata(self):
        """Check if song already has complete metadata."""
        title = self.audiofile.get("TIT2")
        artist = self.audiofile.get("TPE1")
        album = self.audiofile.get("TALB")
        cover = self.audiofile.get("APIC:Cover")

        return bool(title and artist and album and cover)

    def fill_metadata(self):
        """Fill metadata from Spotify. Batches all ID3 changes into single save (2-3x faster)."""
        try:
            title, artist, album, _ = self.song_info()
            title, artist, album, cover = trackInfo.get_track_features(
                title, artist, album, self.file_path
            )

            if title:
                self.audiofile.add(TIT2(encoding=3, text=title))
            if artist:
                self.audiofile.add(TPE1(encoding=3, text=artist))
            if album:
                self.audiofile.add(TALB(encoding=3, text=album))

            self.audiofile.save()

            if cover:
                self.add_album_cover(cover, show=False)
        except Exception as e:
            print(f"Error filling metadata from Spotify: {e}, {self.song_info()}, {self.file_path}")

    def set_cover_from_spotify(self, show_cover=True):
        try:
            if not self.audiofile.get("APIC:Cover"):
                title, artist, album, _ = self.song_info()
                _, _, _, cover = trackInfo.get_track_features(title, artist, album, self.file_path)
                if cover:
                    self.add_album_cover(cover, show=show_cover)
        except Exception as e:
            print(f"Error setting cover from Spotify: {e}")
