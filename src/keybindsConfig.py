import logging
import json
import os
from pathlib import Path
from typing import Dict, Mapping


logger = logging.getLogger(__name__)


DEFAULT_KEYBINDS_JSON = """\
{
  "global": {
    "esc": "app_exit",
    "F1": "show_help",
    "1": "view_switch_0",
    "2": "view_switch_1",
    "3": "view_switch_2"
  },
  "list": {
    "up": "nav_up",
    "down": "nav_down",
    "right": "nav_right",
    "left": "nav_left",
    "s": "playback_toggle",
    "a": "playback_play",
    "p": "playback_stop",
    "n": "playback_next",
    "b": "playback_prev",
    "+": "volume_up",
    "=": "volume_up",
    "-": "volume_down",
    "0": "volume_mute",
    "m": "volume_toggle_mute",
    "l": "loop_toggle",
    "delete": "delete"
  }
}
"""


def get_config_dir() -> Path:
    """
    Return the app config directory.

    Uses XDG_CONFIG_HOME if set; otherwise defaults to ~/.config/metadataEditor.
    """
    xdg = os.environ.get("XDG_CONFIG_HOME")
    if xdg:
        return Path(xdg) / "metadataEditor"
    return Path.home() / ".config" / "metadataEditor"


def get_keybinds_path() -> Path:
    return get_config_dir() / "keybinds.json"


def ensure_default_keybinds_file(path: Path) -> None:
    """Create the keybinds config file with defaults if it doesn't exist."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            path.write_text(DEFAULT_KEYBINDS_JSON, encoding="utf-8")
            logger.info(f"Created default keybinds config at: {path}")
    except Exception as e:
        logger.warning(f"Failed to create default keybinds config at {path}: {e}")


def _validate_keybinds_shape(data: object) -> Dict[str, Dict[str, str]]:
    """
    Ensure the config data is a context->(key->action) mapping of strings.
    Invalid entries are ignored.
    """
    if not isinstance(data, Mapping):
        return {}

    out: Dict[str, Dict[str, str]] = {}
    for ctx, mapping in data.items():
        if not isinstance(ctx, str) or not isinstance(mapping, Mapping):
            continue
        ctx_map: Dict[str, str] = {}
        for key, action in mapping.items():
            if isinstance(key, str) and isinstance(action, str):
                ctx_map[key] = action
        if ctx_map:
            out[ctx] = ctx_map

    return out


def load_keybinds_config() -> Dict[str, Dict[str, str]]:
    """
    Ensure a default keybinds file exists and load it.
    Returns {} on any error (app will use built-in defaults).
    """
    path = get_keybinds_path()
    ensure_default_keybinds_file(path)

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        return _validate_keybinds_shape(raw)
    except FileNotFoundError:
        return {}
    except Exception as e:
        logger.warning(f"Failed to load keybinds config from {path}: {e}")
        return {}

