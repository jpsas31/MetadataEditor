try:
    from src.trackInfo import _REGEX_FILE_EXT, _clean_query
except ImportError:
    import pytest

    pytest.skip("Required dependencies not available", allow_module_level=True)


class TestCleanQuery:
    def test_with_title_and_artist_and_album(self):
        result = _clean_query("Song Title", "Artist Name", "Album Name", "")
        assert result == "song title artist name album name"

    def test_with_title_only(self):
        result = _clean_query("Song Title", "", "", "")
        assert result == "song title  "

    def test_with_none_title_uses_filename(self):
        result = _clean_query("None", "", "", "/path/to/Song Name.mp3")
        assert result == "song name"

    def test_with_empty_title_uses_filename(self):
        result = _clean_query("", "", "", "/path/to/Artist - Song.mp3")
        assert result == "artist song"

    def test_removes_file_extension(self):
        result = _clean_query("", "", "", "/path/to/song.mp3")
        assert result == "song"
        result = _clean_query("", "", "", "/path/to/song.m4a")
        assert result == "song"
        result = _clean_query("", "", "", "/path/to/song.flac")
        assert result == "song"

    def test_removes_official_video(self):
        result = _clean_query("", "", "", "/path/to/Song (official video).mp3")
        assert result == "song "

    def test_removes_official_audio(self):
        result = _clean_query("", "", "", "/path/to/Song (official audio).mp3")
        assert result == "song "

    def test_removes_official_lyric_video(self):
        result = _clean_query("", "", "", "/path/to/Song [official lyric video].mp3")
        assert result == "song "

    def test_removes_feat(self):
        result = _clean_query("", "", "", "/path/to/Song ft. Artist.mp3")
        assert result == "song artist"

    def test_removes_featuring(self):
        result = _clean_query("", "", "", "/path/to/Song featuring Artist.mp3")
        assert result == "song artist"

    def test_removes_parentheses_content(self):
        result = _clean_query("", "", "", "/path/to/Song (Remix).mp3")
        assert result == "song "

    def test_removes_brackets_content(self):
        result = _clean_query("", "", "", "/path/to/Song [Remastered].mp3")
        assert result == "song "

    def test_removes_year(self):
        result = _clean_query("", "", "", "/path/to/Song 2024.mp3")
        assert result == "song "

    def test_removes_special_chars(self):
        result = _clean_query("", "", "", "/path/to/Song!@#$.mp3")
        assert result == "song "

    def test_preserves_ampersand(self):
        result = _clean_query("", "", "", "/path/to/Song & Artist.mp3")
        assert "song" in result
        assert "artist" in result


class TestRegexFileExt:
    def test_matches_mp3(self):
        assert _REGEX_FILE_EXT.search("song.mp3") is not None

    def test_matches_m4a(self):
        assert _REGEX_FILE_EXT.search("song.m4a") is not None

    def test_matches_flac(self):
        assert _REGEX_FILE_EXT.search("song.flac") is not None

    def test_matches_wav(self):
        assert _REGEX_FILE_EXT.search("song.wav") is not None

    def test_matches_ogg(self):
        assert _REGEX_FILE_EXT.search("song.ogg") is not None

    def test_matches_aac(self):
        assert _REGEX_FILE_EXT.search("song.aac") is not None

    def test_case_insensitive(self):
        assert _REGEX_FILE_EXT.search("song.MP3") is not None
        assert _REGEX_FILE_EXT.search("song.FLAC") is not None
