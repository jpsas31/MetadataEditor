from unittest.mock import MagicMock, patch

import pytest

try:
    from src.viewInfo import ViewInfo
except ImportError:
    pytest.skip("viewInfo dependencies not available", allow_module_level=True)


@pytest.fixture
def mock_mp3_editor():
    with patch("src.tagModifier.MP3Editor") as mock_class:
        mock_editor = MagicMock()
        mock_editor.song_info.return_value = ("Title", "Album", "Artist", "Has cover")
        mock_class.return_value = mock_editor
        yield mock_editor


class TestViewInfo:
    @patch("src.viewInfo.os.chdir")
    @patch("src.viewInfo.os.listdir")
    def test_init_loads_mp3_files(self, mock_listdir, mock_chdir):
        mock_listdir.return_value = ["song1.mp3", "song2.mp3", "song3.txt", "song4.mp3"]

        view = ViewInfo("/test/dir")

        mock_chdir.assert_called_once_with("/test/dir")
        assert len(view.canciones) == 3
        assert "song1.mp3" in view.canciones
        assert "song4.mp3" in view.canciones
        assert "song3.txt" not in view.canciones

    @patch("src.viewInfo.os.chdir")
    @patch("src.viewInfo.os.listdir")
    def test_init_sorts_songs(self, mock_listdir, mock_chdir):
        mock_listdir.return_value = ["z_song.mp3", "a_song.mp3", "m_song.mp3"]

        view = ViewInfo("/test/dir")

        assert view.canciones == ["a_song.mp3", "m_song.mp3", "z_song.mp3"]

    @patch("src.viewInfo.os.chdir")
    @patch("src.viewInfo.os.listdir")
    def test_get_dir(self, mock_listdir, mock_chdir):
        mock_listdir.return_value = []

        view = ViewInfo("/test/dir")
        assert view.get_dir() == "/test/dir"

    @patch("src.viewInfo.os.chdir")
    @patch("src.viewInfo.os.listdir")
    def test_add_song(self, mock_listdir, mock_chdir):
        mock_listdir.return_value = ["a.mp3", "b.mp3"]

        view = ViewInfo("/test/dir")
        view.add_song("c.mp3")

        assert "c.mp3" in view.canciones

    @patch("src.viewInfo.os.chdir")
    @patch("src.viewInfo.os.listdir")
    def test_delete_song(self, mock_listdir, mock_chdir):
        mock_listdir.return_value = ["a.mp3", "b.mp3"]

        view = ViewInfo("/test/dir")
        view.delete_song("a.mp3")

        assert "a.mp3" not in view.canciones

    @patch("src.viewInfo.os.chdir")
    @patch("src.viewInfo.os.listdir")
    def test_delete_song_invalidates_cache(self, mock_listdir, mock_chdir):
        mock_listdir.return_value = ["a.mp3", "b.mp3"]

        view = ViewInfo("/test/dir")
        view._metadata_cache["a.mp3"] = ("t", "a", "a", "c")
        view.delete_song("a.mp3")

        assert "a.mp3" not in view._metadata_cache

    @patch("src.viewInfo.os.chdir")
    @patch("src.viewInfo.os.listdir")
    def test_song_info_empty_list(self, mock_listdir, mock_chdir):
        mock_listdir.return_value = []

        view = ViewInfo("/test/dir")
        result = view.song_info(0)

        assert result == ("", "", "", "No Cover")

    @patch("src.viewInfo.os.chdir")
    @patch("src.viewInfo.os.listdir")
    def test_song_info_returns_cached(self, mock_listdir, mock_chdir, mock_mp3_editor):
        mock_listdir.return_value = ["song.mp3"]

        view = ViewInfo("/test/dir")
        view._metadata_cache["song.mp3"] = (
            "Cached Title",
            "Cached Album",
            "Cached Artist",
            "Cached Cover",
        )

        result = view.song_info(0)

        assert result == ("Cached Title", "Cached Album", "Cached Artist", "Cached Cover")

    @patch("src.viewInfo.os.chdir")
    @patch("src.viewInfo.os.listdir")
    def test_song_info_caches_result(self, mock_listdir, mock_chdir, mock_mp3_editor):
        mock_listdir.return_value = ["song.mp3"]

        view = ViewInfo("/test/dir")
        view.song_info(0)

        assert "song.mp3" in view._metadata_cache

    @patch("src.viewInfo.os.chdir")
    @patch("src.viewInfo.os.listdir")
    def test_invalidate_cache(self, mock_listdir, mock_chdir):
        mock_listdir.return_value = []

        view = ViewInfo("/test/dir")
        view._metadata_cache["song.mp3"] = ("t", "a", "a", "c")

        view.invalidate_cache("song.mp3")

        assert "song.mp3" not in view._metadata_cache

    @patch("src.viewInfo.os.chdir")
    @patch("src.viewInfo.os.listdir")
    def test_song_file_name(self, mock_listdir, mock_chdir):
        mock_listdir.return_value = ["song.mp3"]

        view = ViewInfo("/test/dir")
        result = view.song_file_name(0)

        assert result == "song.mp3"

    @patch("src.viewInfo.os.chdir")
    @patch("src.viewInfo.os.listdir")
    def test_song_file_name_empty(self, mock_listdir, mock_chdir):
        mock_listdir.return_value = []

        view = ViewInfo("/test/dir")
        result = view.song_file_name(0)

        assert result == "None"

    @patch("src.viewInfo.os.chdir")
    @patch("src.viewInfo.os.listdir")
    def test_songs_len(self, mock_listdir, mock_chdir):
        mock_listdir.return_value = ["a.mp3", "b.mp3", "c.mp3"]

        view = ViewInfo("/test/dir")
        assert view.songs_len() == 3

    @patch("src.viewInfo.os.chdir")
    @patch("src.viewInfo.os.listdir")
    def test_is_song_true(self, mock_listdir, mock_chdir):
        mock_listdir.return_value = ["song.mp3"]

        view = ViewInfo("/test/dir")
        assert view.is_song("song.mp3") is True

    @patch("src.viewInfo.os.chdir")
    @patch("src.viewInfo.os.listdir")
    def test_is_song_false(self, mock_listdir, mock_chdir):
        mock_listdir.return_value = ["song.mp3"]

        view = ViewInfo("/test/dir")
        assert view.is_song("other.mp3") is False

    @patch("src.viewInfo.os.chdir")
    @patch("src.viewInfo.os.listdir")
    def test_get_current_song(self, mock_listdir, mock_chdir):
        mock_listdir.return_value = ["song.mp3"]

        view = ViewInfo("/test/dir")
        result = view.get_current_song()

        assert result == "/test/dir/song.mp3"

    @patch("src.viewInfo.os.chdir")
    @patch("src.viewInfo.os.listdir")
    def test_get_current_song_empty(self, mock_listdir, mock_chdir):
        mock_listdir.return_value = []

        view = ViewInfo("/test/dir")
        result = view.get_current_song()

        assert result is None

    @patch("src.viewInfo.os.chdir")
    @patch("src.viewInfo.os.listdir")
    def test_get_metadata_cache_returns_copy(self, mock_listdir, mock_chdir):
        mock_listdir.return_value = []

        view = ViewInfo("/test/dir")
        view._metadata_cache["song.mp3"] = ("t", "a", "a", "c")

        cache = view.get_metadata_cache()

        assert "song.mp3" in cache
        assert cache["song.mp3"] == ("t", "a", "a", "c")

        # Ensure it's a copy, not the original
        view._metadata_cache["song.mp3"] = ("t2", "a2", "a2", "c2")
        assert cache["song.mp3"] == ("t", "a", "a", "c")
