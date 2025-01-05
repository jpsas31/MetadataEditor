import os
import re
import shutil
from io import BytesIO
import requests
from mutagen.id3 import ID3, APIC, TIT2, TPE1, TALB
from PIL import Image, ImageFile

import spotifyInfo


class MP3Editor:
    def __init__(self, file_path):
        self.file_path = file_path
        self.audiofile = ID3(file_path)

    def change_artist(self, name):
        self.audiofile.add(TPE1(encoding=3, text=name))
        self.audiofile.save()

    def change_title(self, name):
        self.audiofile.add(TIT2(encoding=3, text=name))
        self.audiofile.save()

    def change_album(self, name):
        self.audiofile.add(TALB(encoding=3, text=name))
        self.audiofile.save()

    def add_album_cover(self, image_link, show=False):
        resp = requests.get(image_link, stream=True)
        dir_path = os.path.dirname(self.file_path)
        album_dir = os.path.join(dir_path, "album")

        if not os.path.exists(album_dir):
            os.makedirs(album_dir)

        cover_path = os.path.join(album_dir, "album.jpg")
        with open(cover_path, "wb") as local_file:
            resp.raw.decode_content = True
            shutil.copyfileobj(resp.raw, local_file)

        with open(cover_path, "rb") as fp:
            image_data = fp.read()

        if show:
            with Image.open(cover_path) as img:
                img.show()

        if not self.audiofile.get("APIC:"):
            self.audiofile.add(
                APIC(encoding=3, mime="image/jpeg", type=3, desc="Cover", data=image_data)
            )
            self.audiofile.save()

    def show_album_cover(self):
        apic_frame = self.audiofile.get("APIC:")
        if apic_frame:
            with Image.open(BytesIO(apic_frame.data)) as img:
                ImageFile.LOAD_TRUNCATED_IMAGES = True
                img.show()

    def remove_album_cover(self):
        self.audiofile.delall("APIC")
        self.audiofile.save()

    def song_info(self):
        title = self.audiofile.get("TIT2").text[0] if self.audiofile.get("TIT2") else ""
        album = self.audiofile.get("TALB").text[0] if self.audiofile.get("TALB") else ""
        artist = self.audiofile.get("TPE1").text[0] if self.audiofile.get("TPE1") else ""
        album_art = "Yes" if self.audiofile.get("APIC:") else "No"

        return title, album, artist, album_art

    def fill_metadata_from_spotify(self, show_cover=True):
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

    def set_cover_from_spotify(self, show_cover=True):
        if not self.audiofile.get("APIC:"):
            query = self._clean_query()
            _, _, _, cover = spotifyInfo.get_Track_Features(query)
            if cover:
                self.add_album_cover(cover, show=show_cover)

    def _clean_query(self):
        title = self.audiofile.get("TIT2").text[0] if self.audiofile.get("TIT2") else ""
        artist = self.audiofile.get("TPE1").text[0] if self.audiofile.get("TPE1") else ""
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
