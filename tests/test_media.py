import pytest

try:
    from src.media import AudioPlayer
except ImportError:
    pytest.skip("miniaudio not available", allow_module_level=True)


class TestAudioPlayer:
    @pytest.fixture
    def player(self):
        return AudioPlayer()

    def test_initial_state(self, player):
        assert player.paused is False
        assert player.current_file is None
        assert player.sound_length == 0
        assert player.play_position == 0
        assert player.is_playing_flag is False

    def test_set_volume_clamps_to_1(self, player):
        player.set_volume(1.5)
        assert player.get_volume() == 1.0

    def test_set_volume_clamps_to_0(self, player):
        player.set_volume(-0.5)
        assert player.get_volume() == 0.0

    def test_set_volume_within_bounds(self, player):
        player.set_volume(0.5)
        assert player.get_volume() == 0.5

    def test_set_loop(self, player):
        player.set_loop(True)
        assert player.get_loop() is True
        player.set_loop(False)
        assert player.get_loop() is False

    def test_get_progress_zero_when_no_duration(self, player):
        progress = player.get_progress()
        assert progress == 0.0

    def test_get_progress_with_duration(self, player):
        player.sound_length = 1000
        player.play_position = 250
        progress = player.get_progress()
        assert progress == 25.0

    def test_get_progress_at_end(self, player):
        player.sound_length = 1000
        player.play_position = 1000
        progress = player.get_progress()
        assert progress == 100.0

    def test_stop_resets_position(self, player):
        player.sound_length = 1000
        player.play_position = 500
        player.stop()
        assert player.play_position == 0

    def test_stop_resets_paused(self, player):
        player.paused = True
        player.stop()
        assert player.paused is False

    def test_stop_resets_playing_flag(self, player):
        player.is_playing_flag = True
        player.stop()
        assert player.is_playing_flag is False
