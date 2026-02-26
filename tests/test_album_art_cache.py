import pytest

from src.albumArtCache import AlbumArtCache


class TestAlbumArtCache:
    @pytest.fixture
    def cache(self, tmp_path):
        return AlbumArtCache(cache_dir=tmp_path, max_memory_cache_size=3)

    def test_default_cache_dir(self):
        cache = AlbumArtCache()
        assert cache.cache_dir.name == "album_art"

    def test_custom_cache_dir(self, tmp_path):
        cache = AlbumArtCache(cache_dir=tmp_path)
        assert cache.cache_dir == tmp_path

    def test_cache_dir_created(self, tmp_path):
        cache = AlbumArtCache(cache_dir=tmp_path / "subdir" / "nested")
        assert cache.cache_dir.exists()

    def test_get_cache_key(self, cache):
        key1 = cache._get_cache_key("/path/song.mp3", b"imagedata", (80, 40))
        key2 = cache._get_cache_key("/path/song.mp3", b"imagedata", (80, 40))
        key3 = cache._get_cache_key("/path/song.mp3", b"differentdata", (80, 40))
        key4 = cache._get_cache_key("/path/other.mp3", b"imagedata", (80, 40))

        assert key1 == key2
        assert key1 != key3
        assert key1 != key4

    def test_cache_key_includes_size(self, cache):
        key1 = cache._get_cache_key("/path/song.mp3", b"data", (80, 40))
        key2 = cache._get_cache_key("/path/song.mp3", b"data", (80, 80))

        assert key1 != key2

    def test_set_and_get(self, cache):
        ascii_art = "test ascii art"
        cache.set("/path/song.mp3", b"imagedata", ascii_art, (80, 40))

        result = cache.get("/path/song.mp3", b"imagedata", (80, 40))
        assert result == ascii_art

    def test_get_returns_none_on_miss(self, cache):
        result = cache.get("/path/nonexistent.mp3", b"data", (80, 40))
        assert result is None

    def test_lru_eviction(self, cache):
        cache.set("/path/song1.mp3", b"data1", "art1", (80, 40))
        cache.set("/path/song2.mp3", b"data2", "art2", (80, 40))
        cache.set("/path/song3.mp3", b"data3", "art3", (80, 40))

        assert len(cache._memory_cache) == 3

        cache.set("/path/song4.mp3", b"data4", "art4", (80, 40))

        assert len(cache._memory_cache) == 3
        assert "/path/song1.mp3" not in cache._cache_access_order

    def test_lru_order_preserved_on_access(self, cache):
        cache.set("/path/song1.mp3", b"data1", "art1", (80, 40))
        cache.set("/path/song2.mp3", b"data2", "art2", (80, 40))

        cache.get("/path/song1.mp3", b"data1", (80, 40))

        cache.set("/path/song3.mp3", b"data3", "art3", (80, 40))
        cache.set("/path/song4.mp3", b"data4", "art4", (80, 40))

        assert "/path/song2.mp3" not in cache._memory_cache

    def test_clear_memory_only(self, cache):
        cache.set("/path/song1.mp3", b"data1", "art1", (80, 40))
        cache.clear(clear_disk=False)

        assert len(cache._memory_cache) == 0
        assert len(cache._cache_access_order) == 0

    def test_clear_disk(self, cache):
        cache.set("/path/song1.mp3", b"data1", "art1", (80, 40))

        cache.clear(clear_disk=True)

        assert len(cache._memory_cache) == 0

    def test_get_cache_stats(self, cache):
        cache.set("/path/song1.mp3", b"data1", "art1", (80, 40))
        cache.set("/path/song2.mp3", b"data2", "art2", (80, 40))

        stats = cache.get_cache_stats()

        assert stats.memory_items == 2
        assert stats.memory_max == 3
        assert stats.disk_items >= 0
        assert stats.disk_size_bytes >= 0
        assert stats.disk_size_mb >= 0

    def test_get_cache_size(self, cache):
        size = cache.get_cache_size()
        assert size >= 0
