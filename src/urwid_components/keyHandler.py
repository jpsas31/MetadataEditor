import logging
from typing import Callable, Dict, Optional

import urwid

from src.singleton import BorgSingleton

state = BorgSingleton()

logger = logging.getLogger(__name__)


class KeyBinding:
    """Represents a keyboard shortcut binding."""

    def __init__(
        self, key: str, description: str, handler: Callable, global_key: bool = False
    ):
        self.key = key
        self.description = description
        self.handler = handler
        self.global_key = global_key

    def __repr__(self):
        scope = "Global" if self.global_key else "Local"
        return f"KeyBinding('{self.key}', '{self.description}', {scope})"


class KeyHandler:
    """Centralized keyboard shortcut management system."""

    def __init__(
        self, config: Dict[str, str] = None, main_loop_manager=None, list_widget=None
    ):
        self.bindings: Dict[str, KeyBinding] = {}
        self.global_bindings: Dict[str, KeyBinding] = {}
        self.config = config or {}
        self.main_loop_manager = main_loop_manager
        self.list_widget = list_widget  # Can be None initially, set later
        self._initialize_bindings()

    def _initialize_bindings(self):
        default_config = {
            "exit": "esc",
            "help": "F1",
            "view_main": "1",
            "view_music": "2",
            "nav_up": "up",
            "nav_down": "down",
            "nav_right": "right",
            "play_toggle": "s",
            "play_select": "a",
            "play_stop": "p",
            "play_next": "n",
            "play_prev": "b",
            "vol_up": "+",
            "vol_up_alt": "=",
            "vol_down": "-",
            "vol_mute": "0",
            "vol_toggle_mute": "m",
            "loop_toggle": "l",
            "delete": "delete",
            "song_select": "song_select",
        }

        # Merge with user config, user config takes precedence
        final_config = {**default_config, **self.config}

        # Global application keys
        self.add_binding(
            final_config["exit"], "Exit application", self._handle_exit, global_key=True
        )

        self.add_binding(
            final_config["exit"],
            "Exit application",
            self._handle_exit,
        )

        self.add_binding(
            final_config["help"], "Show help", self._handle_help, global_key=True
        )
        self.add_binding(
            final_config["view_main"],
            "Switch to main view",
            self._handle_view_switch,
            global_key=True,
            args=(0,),
        )
        self.add_binding(
            final_config["view_music"],
            "Switch to music view",
            self._handle_view_switch,
            global_key=True,
            args=(1,),
        )

        # Global keys (these should work from anywhere)
        self.add_binding(
            "1",
            "Switch to main view",
            self._handle_view_switch,
            global_key=True,
            args=(0,),
        )
        self.add_binding(
            "2",
            "Switch to music view",
            self._handle_view_switch,
            global_key=True,
            args=(1,),
        )
        self.add_binding(
            "3",
            "Switch to view 3",
            self._handle_view_switch,
            global_key=True,
            args=(2,),
        )

        # Navigation keys
        self.add_binding(
            final_config["nav_up"],
            "Move up in list",
            self._handle_navigation,
            args=("up",),
        )
        self.add_binding(
            final_config["nav_down"],
            "Move down in list",
            self._handle_navigation,
            args=("down",),
        )
        self.add_binding(
            final_config["nav_right"], "Focus metadata panel", self._handle_focus_panel
        )

        self.add_binding("left", "Focus song list", self._handle_focus_list)

        # Playback controls
        self.add_binding(
            final_config["play_toggle"],
            "Play/Pause toggle",
            self._handle_playback,
            args=("toggle",),
        )
        self.add_binding(
            final_config["play_select"],
            "Play selected song",
            self._handle_playback,
            args=("play",),
        )
        self.add_binding(
            final_config["play_stop"],
            "Stop playback",
            self._handle_playback,
            args=("stop",),
        )
        self.add_binding(
            final_config["play_next"],
            "Next song",
            self._handle_playback,
            args=("next",),
        )
        self.add_binding(
            final_config["play_prev"],
            "Previous song",
            self._handle_playback,
            args=("prev",),
        )

        # Volume controls
        self.add_binding(
            final_config["vol_up"], "Volume up", self._handle_volume, args=("up",)
        )
        self.add_binding(
            final_config["vol_up_alt"],
            "Volume up (alternative)",
            self._handle_volume,
            args=("up",),
        )
        self.add_binding(
            final_config["vol_down"], "Volume down", self._handle_volume, args=("down",)
        )
        self.add_binding(
            final_config["vol_mute"], "Mute", self._handle_volume, args=("mute",)
        )
        self.add_binding(
            final_config["vol_toggle_mute"],
            "Toggle mute",
            self._handle_volume,
            args=("toggle_mute",),
        )

        # Loop control
        self.add_binding(
            final_config["loop_toggle"], "Toggle loop mode", self._handle_loop
        )

        # File operations
        self.add_binding(final_config["delete"], "Delete song", self._handle_delete)

        # Song selection (for button clicks)
        self.add_binding(
            final_config["song_select"], "Select song", self._handle_song_select
        )

    def add_binding(
        self,
        key: str,
        description: str,
        handler: Callable,
        global_key: bool = False,
        args: tuple = None,
    ) -> None:
        """Add a new key binding."""
        # Validate inputs
        if not isinstance(key, str) or not key:
            raise ValueError(f"Invalid key: '{key}'. Key must be a non-empty string.")

        if not isinstance(description, str) or not description:
            raise ValueError("Description must be a non-empty string.")

        if not callable(handler):
            raise ValueError("Handler must be callable.")

        if key in self.global_bindings or key in self.bindings:
            logger = logging.getLogger(__name__)
            logger.warning(f"Overriding existing key binding for '{key}'")

        binding = KeyBinding(key, description, handler, global_key)
        binding.args = args or ()

        if global_key:
            self.global_bindings[key] = binding
        else:
            self.bindings[key] = binding

    def remove_binding(self, key: str, global_key: bool = False) -> bool:
        """Remove a key binding. Returns True if binding was found and removed."""
        if global_key and key in self.global_bindings:
            del self.global_bindings[key]
            return True
        elif not global_key and key in self.bindings:
            del self.bindings[key]
            return True
        return False

    def get_binding(self, key: str, global_key: bool = False) -> Optional[KeyBinding]:
        """Get a key binding by key."""
        if global_key and key in self.global_bindings:
            return self.global_bindings[key]
        elif not global_key and key in self.bindings:
            return self.bindings[key]
        return None

    def handle_key(self, key: str, widget_context: str = "global") -> bool:
        """
        Handle a key press. Returns True if key was handled, False otherwise.
        widget_context: "global" for global keys, or specific widget name
        """
        # Validate input
        if not isinstance(key, str) or not key:
            return False

        # Try global bindings first
        if key in self.global_bindings:
            binding = self.global_bindings[key]
            try:
                binding.handler(*binding.args)
                return True
            except Exception as e:
                logger = logging.getLogger(__name__)
                logger.error(f"Error handling global key '{key}': {e}")
                return False

        # Try local bindings if not in global context
        if widget_context != "global" and key in self.bindings:
            binding = self.bindings[key]
            try:
                binding.handler(*binding.args)
                return True
            except Exception as e:
                logger = logging.getLogger(__name__)
                logger.error(f"Error handling local key '{key}': {e}")
                return False

        return False

    def get_help_text(self) -> str:
        """Get formatted help text showing all available shortcuts."""
        help_lines = ["Keyboard Shortcuts:", ""]

        # Global shortcuts
        if self.global_bindings:
            help_lines.append("Global (work from any widget):")
            for key, binding in sorted(self.global_bindings.items()):
                help_lines.append(f"  {key:15} - {binding.description}")
            help_lines.append("")

        # Local shortcuts
        if self.bindings:
            help_lines.append("Navigation & Media (local keys):")
            for key, binding in sorted(self.bindings.items()):
                help_lines.append(f"  {key:15} - {binding.description}")

        return "\n".join(help_lines)

    # Handler methods
    def _handle_exit(self):
        """Handle exit key."""
        if self.main_loop_manager:
            self.main_loop_manager.state.stop_event.set()
            raise urwid.ExitMainLoop()

    def _handle_help(self):
        """Handle help key."""
        # Show help in a popup or status message
        if self.main_loop_manager and hasattr(self.main_loop_manager, "view_manager"):
            main_view = self.main_loop_manager.view_manager.get_view("main")
            if main_view and hasattr(main_view, "footer"):
                help_bindings = [f"{k}" for k in list(self.global_bindings.keys())[:3]]
                main_view.footer.set_status("Help: " + " | ".join(help_bindings))

    def _handle_view_switch(self, view_index: int):
        """Handle view switching."""
        if self.main_loop_manager:
            self.main_loop_manager.change_view(view_index)

    def _handle_navigation(self, direction: str):
        """Handle navigation with wrap-around."""
        if self.list_widget:
            cursor_pos = self.list_widget.get_focus()[1]
            max_pos = len(self.list_widget.body) - 1

            if direction == "up":
                new_pos = cursor_pos - 1
                # Wrap around to bottom if at top
                if new_pos < 0:
                    new_pos = max_pos
            elif direction == "down":
                new_pos = cursor_pos + 1
                # Wrap around to top if at bottom
                if new_pos > max_pos:
                    new_pos = 0
            else:
                return

            # Update metadata for new position and move focus
            self.list_widget._move_focus(new_pos)
            self.list_widget.set_focus(new_pos)

    def _handle_focus_panel(self):
        """Handle panel focusing."""
        if self.list_widget and hasattr(self.list_widget, "display"):
            display = self.list_widget.display
            if display and hasattr(display, "columns"):
                display.columns.focus_col = 1

    def _handle_focus_list(self):
        """Handle focusing back to song list."""
        if self.list_widget and hasattr(self.list_widget, "display"):
            display = self.list_widget.display
            if display and hasattr(display, "columns"):
                display.columns.focus_col = 0

    def _handle_playback(self, action: str):
        """Handle playback controls."""
        if not self.main_loop_manager or not hasattr(
            self.main_loop_manager, "audio_player"
        ):
            return

        player = self.main_loop_manager.audio_player

        if action == "toggle":
            player.resume_pause()
        elif action == "play":
            if self.list_widget:
                cursor_pos = self.list_widget.get_focus()[1]
                self.list_widget._play_song(cursor_pos)
        elif action == "stop":
            player.stop()
        elif action == "next":
            if self.list_widget:
                cursor_pos = self.list_widget.get_focus()[1]
                # Use the wrap-around version
                next_pos = cursor_pos + 1
                max_pos = len(self.list_widget.body) - 1
                if next_pos > max_pos:
                    next_pos = 0
                self.list_widget.set_focus(next_pos)
                title, album, artist, album_art = state.viewInfo.songInfo(next_pos)
                self.list_widget._update_metadata_panel(
                    next_pos, title, album, artist, album_art
                )
                self.list_widget._play_song(next_pos)
        elif action == "prev":
            if self.list_widget:
                cursor_pos = self.list_widget.get_focus()[1]
                # Use the wrap-around version
                prev_pos = cursor_pos - 1
                max_pos = len(self.list_widget.body) - 1
                if prev_pos < 0:
                    prev_pos = max_pos
                self.list_widget.set_focus(prev_pos)
                title, album, artist, album_art = state.viewInfo.songInfo(prev_pos)
                self.list_widget._update_metadata_panel(
                    prev_pos, title, album, artist, album_art
                )
                self.list_widget._play_song(prev_pos)

    def _handle_volume(self, action: str):
        """Handle volume controls."""
        if not self.main_loop_manager or not hasattr(
            self.main_loop_manager, "audio_player"
        ):
            return

        player = self.main_loop_manager.audio_player

        if action == "up":
            current_vol = player.get_volume()
            player.set_volume(min(1.0, current_vol + 0.1))
        elif action == "down":
            current_vol = player.get_volume()
            player.set_volume(max(0.0, current_vol - 0.1))
        elif action == "mute":
            player.set_volume(0.0)
        elif action == "toggle_mute":
            if player.get_volume() > 0:
                self._last_volume = player.get_volume()
                player.set_volume(0.0)
            else:
                player.set_volume(getattr(self, "_last_volume", 1.0))

        # Show volume feedback
        if self.main_loop_manager and hasattr(self.main_loop_manager, "view_manager"):
            main_view = self.main_loop_manager.view_manager.get_view("main")
            if main_view and hasattr(main_view, "footer"):
                volume = int(player.get_volume() * 100)
                status = "Muted" if volume == 0 else f"Volume: {volume}%"
                main_view.footer.set_status(status)

                import threading

                def clear_status():
                    import time

                    time.sleep(2)
                    if hasattr(main_view, "footer"):
                        main_view.footer.clear_status()

                threading.Thread(target=clear_status, daemon=True).start()

    def _handle_loop(self):
        """Handle loop toggle."""
        if not self.main_loop_manager or not hasattr(
            self.main_loop_manager, "audio_player"
        ):
            return

        player = self.main_loop_manager.audio_player
        player.set_loop(not player.get_loop())

        # Show loop feedback
        if self.main_loop_manager and hasattr(self.main_loop_manager, "view_manager"):
            main_view = self.main_loop_manager.view_manager.get_view("main")
            if main_view and hasattr(main_view, "footer"):
                loop_enabled = player.get_loop()
                status = "Loop: ON" if loop_enabled else "Loop: OFF"
                main_view.footer.set_status(status)

                import threading

                def clear_status():
                    import time

                    time.sleep(2)
                    if hasattr(main_view, "footer"):
                        main_view.footer.clear_status()

                threading.Thread(target=clear_status, daemon=True).start()

    def _handle_delete(self):
        """Handle song deletion."""
        if self.list_widget:
            cursor_pos = self.list_widget.get_focus()[1]
            self.list_widget._delete_song(cursor_pos)

    def _handle_song_select(self, song_name):
        """Handle song selection."""
        if self.main_loop_manager:
            self.main_loop_manager.change_view(song_name)

    def validate_config(self, config: Dict[str, str]) -> Dict[str, str]:
        """Validate a key configuration dictionary."""
        errors = []

        # Check for required keys
        required_keys = [
            "exit",
            "help",
            "view_main",
            "view_music",
            "nav_up",
            "nav_down",
            "play_toggle",
            "play_select",
            "vol_up",
            "vol_down",
        ]

        for req_key in required_keys:
            if req_key not in config:
                errors.append(f"Missing required configuration key: '{req_key}'")
            elif not isinstance(config[req_key], str) or not config[req_key]:
                errors.append(
                    f"Invalid value for '{req_key}': must be non-empty string"
                )

        # Check for duplicate key assignments
        key_usage = {}
        for config_key, key_value in config.items():
            if key_value in key_usage:
                errors.append(
                    f"Duplicate key assignment: '{key_value}' used for both '{key_usage[key_value]}' and '{config_key}'"
                )
            key_usage[key_value] = config_key

        if errors:
            raise ValueError(
                "Configuration validation failed:\n"
                + "\n".join(f"  - {err}" for err in errors)
            )

        return config

    def save_config(self, filepath: str) -> None:
        """Save current configuration to file."""
        import json

        try:
            with open(filepath, "w") as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to save config to {filepath}: {e}")

    def load_config(self, filepath: str) -> None:
        """Load configuration from file."""
        import json

        try:
            with open(filepath, "r") as f:
                config = json.load(f)
            self.config = self.validate_config(config)
            # Reinitialize bindings with new config
            self.bindings.clear()
            self.global_bindings.clear()
            self._initialize_bindings()
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to load config from {filepath}: {e}")

    def get_config_summary(self) -> str:
        """Get a summary of current key configuration."""
        lines = ["Current Key Configuration:"]
        for category in ["Global Keys", "Local Keys"]:
            lines.append(f"\n{category}:")
            bindings_dict = (
                self.global_bindings if category == "Global Keys" else self.bindings
            )
            for key, binding in sorted(bindings_dict.items()):
                lines.append(f"  {key:12} -> {binding.description}")

        return "\n".join(lines)
