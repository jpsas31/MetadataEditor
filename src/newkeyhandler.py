import logging
from typing import Callable, Dict

logger = logging.getLogger(__name__)


class KeyBinding:
    """Represents a keyboard shortcut binding."""

    def __init__(
        self, key: str, description: str, action: Callable, global_key: bool = False
    ):
        self.key = key
        self.description = description
        self.action = action  # Final 0-argument callable
        self.global_key = global_key

    def __repr__(self):
        scope = "Global" if self.global_key else "Local"
        return f"KeyBinding('{self.key}', '{self.description}', {scope})"


class KeyHandler:
    """Centralized keyboard shortcut management system using Registry pattern."""

    def __init__(self, config: Dict[str, str] = None):
        self.key_to_action: Dict[str, str] = {}  # Maps keys to action names
        self.global_key_to_action: Dict[str, str] = {}  # Global keys to actions
        self.action_registry: Dict[str, Callable] = {}  # Maps action names to handlers
        self.config = config or {}
        self._initialize_bindings()

    def _initialize_bindings(self):
        """Initialize key-to-action mappings using configuration."""
        default_config = {
            "exit": "esc",
            "help": "F1",
            "view_main": "1",
            "view_music": "2",
            "nav_up": "up",
            "nav_down": "down",
            "nav_right": "right",
            "nav_left": "left",
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
        }

        # Merge with user config, user config takes precedence
        final_config = {**default_config, **self.config}

        # Global application keys
        self.global_key_to_action[final_config["exit"]] = "app_exit"
        self.global_key_to_action[final_config["help"]] = "show_help"

        # View switching (global)
        self.global_key_to_action[final_config["view_main"]] = "view_switch_0"
        self.global_key_to_action[final_config["view_music"]] = "view_switch_1"
        self.global_key_to_action["3"] = "view_switch_2"

        # Navigation keys (local)
        self.key_to_action[final_config["nav_up"]] = "nav_up"
        self.key_to_action[final_config["nav_down"]] = "nav_down"
        self.key_to_action[final_config["nav_right"]] = "focus_metadata"
        self.key_to_action[final_config["nav_left"]] = "focus_list"

        # Playback controls (local)
        self.key_to_action[final_config["play_toggle"]] = "playback_toggle"
        self.key_to_action[final_config["play_select"]] = "playback_play"
        self.key_to_action[final_config["play_stop"]] = "playback_stop"
        self.key_to_action[final_config["play_next"]] = "playback_next"
        self.key_to_action[final_config["play_prev"]] = "playback_prev"

        # Volume controls (local)
        self.key_to_action[final_config["vol_up"]] = "volume_up"
        self.key_to_action[final_config["vol_up_alt"]] = "volume_up"
        self.key_to_action[final_config["vol_down"]] = "volume_down"
        self.key_to_action[final_config["vol_mute"]] = "volume_mute"
        self.key_to_action[final_config["vol_toggle_mute"]] = "volume_toggle_mute"

        # Loop control (local)
        self.key_to_action[final_config["loop_toggle"]] = "loop_toggle"

        # File operations (local)
        self.key_to_action[final_config["delete"]] = "delete_song"

    def register_action(self, action_name: str, handler: Callable) -> None:
        """Register a handler for a named action."""
        if not isinstance(action_name, str) or not action_name:
            raise ValueError("Action name must be a non-empty string.")

        if not callable(handler):
            raise ValueError("Handler must be callable.")

        self.action_registry[action_name] = handler

    def unregister_action(self, action_name: str) -> bool:
        """Remove an action handler. Returns True if found and removed."""
        if action_name in self.action_registry:
            del self.action_registry[action_name]
            return True
        return False

    def get_registered_actions(self) -> Dict[str, Callable]:
        """Get all registered actions."""
        return self.action_registry.copy()

    def handle_key(self, key: str, widget_context: str = "global") -> bool:
        """
        Handle a key press using the Registry pattern.
        Returns True if key was handled, False otherwise.
        """
        # Validate input
        if not isinstance(key, str) or not key:
            return False

        # Try global keys first
        if key in self.global_key_to_action:
            action_name = self.global_key_to_action[key]
            if action_name in self.action_registry:
                try:
                    self.action_registry[action_name]()
                    return True
                except Exception as e:
                    logger.error(f"Error handling global action '{action_name}': {e}")
                    return False

        # Try local keys
        if key in self.key_to_action:
            action_name = self.key_to_action[key]
            if action_name in self.action_registry:
                try:
                    self.action_registry[action_name]()
                    return True
                except Exception as e:
                    logger.error(f"Error handling local action '{action_name}': {e}")
                    return False

        return False

    def get_help_text(self) -> str:
        """Get formatted help text showing all available shortcuts."""
        help_lines = ["Keyboard Shortcuts:", ""]

        # Global shortcuts
        if self.global_key_to_action:
            help_lines.append("Global (work from any widget):")
            for key in sorted(self.global_key_to_action.keys()):
                action_name = self.global_key_to_action[key]
                description = self._get_action_description(action_name)
                help_lines.append(f"  {key:15} - {description}")
            help_lines.append("")

        # Local shortcuts
        if self.key_to_action:
            help_lines.append("Navigation & Media (local keys):")
            for key in sorted(self.key_to_action.keys()):
                action_name = self.key_to_action[key]
                description = self._get_action_description(action_name)
                help_lines.append(f"  {key:15} - {description}")

        return "\n".join(help_lines)

    def _get_action_description(self, action_name: str) -> str:
        """Get human-readable description for an action."""
        descriptions = {
            "app_exit": "Exit application",
            "show_help": "Show help",
            "view_switch_0": "Switch to main view",
            "view_switch_1": "Switch to music view",
            "view_switch_2": "Switch to view 3",
            "nav_up": "Move up in list",
            "nav_down": "Move down in list",
            "focus_metadata": "Focus metadata panel",
            "focus_list": "Focus song list",
            "playback_toggle": "Play/Pause toggle",
            "playback_play": "Play selected song",
            "playback_stop": "Stop playback",
            "playback_next": "Next song",
            "playback_prev": "Previous song",
            "volume_up": "Volume up",
            "volume_down": "Volume down",
            "volume_mute": "Mute",
            "volume_toggle_mute": "Toggle mute",
            "loop_toggle": "Toggle loop mode",
            "delete_song": "Delete song",
        }
        return descriptions.get(action_name, action_name)

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
