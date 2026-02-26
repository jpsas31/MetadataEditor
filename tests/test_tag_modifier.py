from unittest.mock import MagicMock, patch

import pytest

try:
    from src.tagModifier import MP3Editor
except ImportError:
    pytest.skip("tagModifier dependencies not available", allow_module_level=True)


@pytest.fixture
def mock_audiofile():
    with patch("src.tagModifier.ID3") as mock_id3:
        mock_instance = MagicMock()
        mock_id3.return_value = mock_instance
        yield mock_instance


class TestMP3Editor:
    def test_init_opens_file(self, mock_audiofile):
        editor = MP3Editor("/path/to/song.mp3")
        assert editor.file_path == "/path/to/song.mp3"

    def test_change_artist(self, mock_audiofile):
        editor = MP3Editor("/path/to/song.mp3")
        editor.change_artist("Test Artist")
        mock_audiofile.add.assert_called()
        mock_audiofile.save.assert_called()

    def test_change_artist_no_save(self, mock_audiofile):
        editor = MP3Editor("/path/to/song.mp3")
        editor.change_artist("Test Artist", save=False)
        mock_audiofile.add.assert_called()
        mock_audiofile.save.assert_not_called()

    def test_change_title(self, mock_audiofile):
        editor = MP3Editor("/path/to/song.mp3")
        editor.change_title("Test Title")
        mock_audiofile.add.assert_called()
        mock_audiofile.save.assert_called()

    def test_change_album(self, mock_audiofile):
        editor = MP3Editor("/path/to/song.mp3")
        editor.change_album("Test Album")
        mock_audiofile.add.assert_called()
        mock_audiofile.save.assert_called()

    def test_save_calls_save_method(self, mock_audiofile):
        editor = MP3Editor("/path/to/song.mp3")
        editor.save()
        mock_audiofile.save.assert_called_once()

    @patch("src.tagModifier.requests.get")
    def test_add_album_cover_success(self, mock_get, mock_audiofile):
        mock_response = MagicMock()
        mock_response.content = b"fake image data"
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        mock_audiofile.get.return_value = None

        editor = MP3Editor("/path/to/song.mp3")
        editor.add_album_cover("http://example.com/cover.jpg")

        mock_get.assert_called_once()
        mock_audiofile.add.assert_called()
        mock_audiofile.save.assert_called()

    @patch("src.tagModifier.requests.get")
    def test_add_album_cover_when_already_exists(self, mock_get, mock_audiofile):
        mock_response = MagicMock()
        mock_response.content = b"fake image data"
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        mock_audiofile.get.return_value = MagicMock()

        editor = MP3Editor("/path/to/song.mp3")
        editor.add_album_cover("http://example.com/cover.jpg")

        mock_get.assert_called_once()
        mock_audiofile.add.assert_not_called()

    def test_get_cover_returns_image(self, mock_audiofile):
        mock_apic = MagicMock()
        mock_apic.data = b"fake image bytes"
        mock_audiofile.get.return_value = mock_apic

        with patch("src.tagModifier.Image.open") as mock_image_open:
            mock_image = MagicMock()
            mock_image_open.return_value = mock_image

            editor = MP3Editor("/path/to/song.mp3")
            result = editor.get_cover()

            assert result == mock_image

    def test_get_cover_returns_none(self, mock_audiofile):
        mock_audiofile.get.return_value = None

        editor = MP3Editor("/path/to/song.mp3")
        result = editor.get_cover()

        assert result is None

    def test_remove_album_cover(self, mock_audiofile):
        editor = MP3Editor("/path/to/song.mp3")
        editor.remove_album_cover()
        mock_audiofile.delall.assert_called_with("APIC:Cover")
        mock_audiofile.save.assert_called()

    def test_song_info_returns_tuple(self, mock_audiofile):
        mock_title = MagicMock()
        mock_title.text = ["Test Title"]
        mock_album = MagicMock()
        mock_album.text = ["Test Album"]
        mock_artist = MagicMock()
        mock_artist.text = ["Test Artist"]

        mock_audiofile.get.side_effect = lambda x: {
            "TIT2": mock_title,
            "TALB": mock_album,
            "TPE1": mock_artist,
            "APIC:Cover": "",
        }.get(x)

        editor = MP3Editor("/path/to/song.mp3")
        title, album, artist, cover = editor.song_info()

        assert title == "Test Title"
        assert album == "Test Album"
        assert artist == "Test Artist"

    def test_has_metadata_true_when_complete(self, mock_audiofile):
        mock_audiofile.get.return_value = MagicMock()

        editor = MP3Editor("/path/to/song.mp3")
        result = editor.has_metadata()

        assert result is True

    def test_has_metadata_false_when_incomplete(self, mock_audiofile):
        mock_audiofile.get.return_value = None

        editor = MP3Editor("/path/to/song.mp3")
        result = editor.has_metadata()

        assert result is False
