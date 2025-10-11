import os
import re
from io import BytesIO

import requests
from mutagen.id3 import APIC, ID3, TALB, TIT2, TPE1
from PIL import Image, ImageFile

import src.spotifyInfo as spotifyInfo


class MP3Editor:
    def __init__(self, file_path):
        self.file_path = file_path
        self.audiofile = ID3(file_path)

    def change_artist(self, text):
        self.audiofile.add(TPE1(encoding=3, text=text))
        self.audiofile.save()

    def change_title(self, text):
        self.audiofile.add(TIT2(encoding=3, text=text))
        self.audiofile.save()

    def change_album(self, text):
        self.audiofile.add(TALB(encoding=3, text=text))
        self.audiofile.save()

    def add_album_cover(self, image_link, show=False):
        try:
            resp = requests.get(image_link, stream=True, timeout=10)
            resp.raise_for_status()

            image_data = resp.content

            if show:
                with Image.open(BytesIO(image_data)) as img:
                    img.show()

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
        try:
            apic_frame = self.audiofile.get("APIC:Cover")
            if apic_frame:
                with Image.open(BytesIO(apic_frame.data)) as img:
                    ImageFile.LOAD_TRUNCATED_IMAGES = True
                    img.show()
        except Exception as e:
            print(f"Error showing album cover: {e}")

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
        artist = (
            self.audiofile.get("TPE1").text[0] if self.audiofile.get("TPE1") else ""
        )
        album_art = False if self.audiofile.get("APIC:Cover") == "" else True
        album_art = "Has cover" if album_art else "No Cover"
        return title, album, artist, album_art

    def fill_metadata_from_spotify(self, show_cover=True):
        try:
            query = self._clean_query()
            title, artist, album, cover = spotifyInfo.get_Track_Features(query)

            if title:
                self.audiofile.add(TIT2(encoding=3, text=title))
            if artist:
                self.audiofile.add(TPE1(encoding=3, text=artist))
            if album:
                self.audiofile.add(TALB(encoding=3, text=album))
            self.audiofile.save()

            if cover:
                self.add_album_cover(cover, show=show_cover)
        except Exception as e:
            print(f"Error filling metadata from Spotify: {e}")

    def set_cover_from_spotify(self, show_cover=True):
        try:
            if not self.audiofile.get("APIC:Cover"):
                query = self._clean_query()
                _, _, _, cover = spotifyInfo.get_Track_Features(query)
                if cover:
                    self.add_album_cover(cover, show=show_cover)
        except Exception as e:
            print(f"Error setting cover from Spotify: {e}")

    def _clean_query(self):
        title = self.audiofile.get("TIT2").text[0] if self.audiofile.get("TIT2") else ""
        artist = (
            self.audiofile.get("TPE1").text[0] if self.audiofile.get("TPE1") else ""
        )
        album = self.audiofile.get("TALB").text[0] if self.audiofile.get("TALB") else ""

        if title and title != "None":
            return " ".join([title, artist, album]).lower()
        else:
            query = os.path.basename(self.file_path).lower()
            query = (
                query.replace(".mp3", "")
                .replace("by", "")
                .replace("studio", "")
                .replace("live", "")
            )
            query = re.sub(r"\(.*?\)", "", query, flags=re.I)
            query = re.sub(r"20[0-9]+[0-9]+", "", query, flags=re.I)
            query = re.sub(r"『.*?』", "", query, flags=re.I)
            query = re.sub(r"\[.*?\]", "", query, flags=re.I)
            query = re.sub(r"ft\.?.*", "", query, flags=re.I)
            query = re.sub(r"feat\.?.*", "", query, flags=re.I)
            query = re.sub(r"[^a-zA-Z0-9&\ ]+", " ", query, flags=re.I)
            return query.lower()
