import subprocess
import time
from threading import Event, Lock, Thread

import miniaudio


class AudioPlayer:
    """
    Enhanced audio player using miniaudio with advanced controls.

    Features:
    - Play/Pause/Stop
    - Seek to position
    - Volume control (0.0 to 1.0)
    - Playback speed control
    - Loop mode
    - Accurate position tracking
    """

    def __init__(self):
        self.paused = False
        self.current_file = None
        self.sound_length = 0
        self.play_position = 0
        self.is_playing_flag = False
        self.device = None
        self.decoded_audio = None
        self.lock = Lock()
        self._start_time = 0
        self._pause_time = 0
        self._volume = 1.0  # Volume level (0.0 to 1.0)
        self._playback_speed = 1.0  # Playback speed multiplier
        self._loop_enabled = False  # Loop playback
        self._sample_rate = 44100
        self._num_channels = 2
        self._sample_width = 2
        self.ffmpegInstance = None
        self.stop_event = Event()

    def set_media(self, file_name):
        """Load and play an audio file using streaming for better performance."""
        # Stop current playback immediately
        self.stop()

        # Load and start playback in background thread
        def load_and_play():
            try:
                file_info = miniaudio.get_file_info(file_name)

                with self.lock:
                    self.current_file = file_name
                    self.sound_length = int(file_info.duration * 1000)
                    self.play_position = 0
                    self.paused = False
                    self._start_time = time.time() * 1000
                    self._sample_rate = file_info.sample_rate
                    self._num_channels = file_info.nchannels

                    # Decode only what we need for seeking (lazy loading)
                    self.decoded_audio = None

                # Start streaming playback
                self._start_streaming_playback()

            except Exception as e:
                print(f"Error loading media file {file_name}: {e}")

                self.is_playing_flag = False

        # Run in daemon thread so it doesn't block UI
        Thread(target=load_and_play, daemon=True).start()

    def _start_playback(self, start_frame=0):
        """Internal method to start or restart playback from a specific frame."""
        try:
            if self.device:
                try:
                    self.device.stop()
                    self.device.close()
                except Exception:
                    pass

            # Create playback device
            self.device = miniaudio.PlaybackDevice(
                sample_rate=self._sample_rate, nchannels=self._num_channels
            )
            self.is_playing_flag = True
            if self.ffmpegInstance:
                self.ffmpegInstance.terminate()
                self.ffmpegInstance = None

            self.ffmpeg_stream_pcm(start_frame)

        except Exception as e:
            print(f"Error starting playback: {e}")
            self.is_playing_flag = False

    def _start_streaming_playback(self):
        """Start playback using streaming mode for better performance."""
        try:
            if self.device:
                try:
                    self.device.stop()
                    self.device.close()
                except Exception:
                    pass

            # Create playback device
            self.device = miniaudio.PlaybackDevice(
                sample_rate=self._sample_rate, nchannels=self._num_channels
            )
            self.is_playing_flag = True

            if self.ffmpegInstance:
                self.ffmpegInstance.terminate()
                self.ffmpegInstance = None

            self.ffmpeg_stream_pcm(0)

        except Exception as e:
            print(f"Error starting streaming playback: {e}")
            self.is_playing_flag = False

    def play(self):
        """Start or resume playback (non-blocking)."""

        def do_play():
            with self.lock:
                if self.paused and self.device:
                    resume_time = time.time() * 1000
                    self._start_time += resume_time - self._pause_time
                    self.paused = False

                    current_pos_ms = self._pause_time - self._start_time
                    start_frame = int((current_pos_ms / 1000.0))
                    self._start_playback(start_frame)
                elif not self.is_playing_flag and self.current_file:
                    pass

            if not self.paused and not self.is_playing_flag and self.current_file:
                self.set_media(self.current_file)

        Thread(target=do_play, daemon=True).start()

    def pause(self):
        """Pause playback."""
        with self.lock:
            if self.is_playing_flag and not self.paused:
                self._pause_time = time.time() * 1000
                self.paused = True
                self.is_playing_flag = False
                try:
                    if self.device:
                        self.device.stop()
                except Exception:
                    pass

    def resume_pause(self):
        """Toggle between play and pause."""
        with self.lock:
            if self.paused or not self.is_playing_flag:
                pass
        if self.paused or not self.is_playing_flag:
            self.play()
        else:
            self.pause()

    def stop(self):
        """Stop playback and reset position."""
        with self.lock:
            self.is_playing_flag = False
            self.paused = False
            if self.device:
                try:
                    self.device.stop()
                    self.device.close()
                except Exception:
                    pass
                self.device = None
            self.play_position = 0

    def set_volume(self, volume):
        self._volume = max(0.0, min(1.0, volume))

    def get_volume(self):
        return self._volume

    def set_loop(self, enabled):
        self._loop_enabled = enabled

    def get_loop(self):
        return self._loop_enabled

    def get_play_position(self):
        """Get current playback position in milliseconds."""
        if self.paused:
            return int(self._pause_time - self._start_time)
        if self.is_playing_flag:
            return int((time.time() * 1000) - self._start_time)
        return self.play_position

    def get_duration(self):
        """Get total duration in milliseconds."""
        return self.sound_length

    def get_progress(self):
        """Get playback progress as percentage"""
        if self.sound_length == 0:
            return 0.0
        return (self.get_play_position() / self.sound_length) * 100.0

    def is_playing(self):
        """Check if audio is currently playing."""
        with self.lock:
            if not self._loop_enabled:
                if self.is_playing_flag and self.get_play_position() >= self.sound_length:
                    self.is_playing_flag = False
            return self.is_playing_flag and not self.paused

    def thread_play(self, update_position):
        """Thread loop for updating playback position."""
        while not self.stop_event.is_set():
            if self.is_playing():
                update_position(self.sound_length, self.get_play_position())
            time.sleep(0.01)

        self.stop()

    def stream_pcm(self, source):
        required_frames = yield b""
        while True:
            required_bytes = required_frames * self._num_channels * self._sample_width
            sample_data = source.read(required_bytes)
            if not sample_data:
                break

            required_frames = yield sample_data

    def ffmpeg_stream_pcm(self, start_frame):
        self.ffmpegInstance = subprocess.Popen(
            [
                "ffmpeg",
                "-v",
                "fatal",
                "-hide_banner",
                "-nostdin",
                "-i",
                self.current_file,
                "-ss",
                str(start_frame),
                "-f",
                "s16le",
                "-acodec",
                "pcm_s16le",
                "-ac",
                str(self._num_channels),
                "-ar",
                str(self._sample_rate),
                "-",
            ],
            stdin=None,
            stdout=subprocess.PIPE,
        )

        stream = self.stream_pcm(self.ffmpegInstance.stdout)
        next(stream)
        self.device.start(stream)
