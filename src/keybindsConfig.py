import os
import re
from collections.abc import Mapping
from pathlib import Path

from src.logging_config import setup_logging

logger = setup_logging(__name__)

try:
    import tomllib  # Python 3.11+
except ModuleNotFoundError:  # pragma: no cover
    tomllib = None


def _repo_default_keybinds_path() -> Path:
    return Path(__file__).resolve().with_name("default_keybinds.toml")


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
    return get_config_dir() / "keybinds.toml"


def _is_valid_toml_key(key: str) -> bool:
    return bool(re.fullmatch(r"[A-Za-z0-9_-]+", key))


def _toml_quote_key(key: str) -> str:
    if _is_valid_toml_key(key):
        return key
    return '"' + key.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _toml_quote_value(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _keybinds_to_toml(data: dict[str, dict[str, str]]) -> str:
    """Serialize context->(key->action) mapping into a simple TOML string."""
    lines: list[str] = [
        "# MetadataEditor keybinds",
        "# Contexts: [global], [list], ...",
        "",
    ]

    for ctx in sorted(data.keys()):
        lines.append(f"[{ctx}]")
        mapping = data.get(ctx, {})
        for key in sorted(mapping.keys()):
            action = mapping[key]
            lines.append(f"{_toml_quote_key(key)} = {_toml_quote_value(action)}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def _migrate_json_to_toml_if_present(toml_path: Path) -> bool:
    """
    If an old keybinds.json exists, convert it into keybinds.toml.
    Returns True if migration succeeded.
    """
    json_path = toml_path.with_suffix(".json")
    if not json_path.exists():
        return False

    try:
        import json  # local import to keep TOML path clean

        raw = json.loads(json_path.read_text(encoding="utf-8"))
        data = _validate_keybinds_shape(raw)
        if not data:
            return False

        toml_path.write_text(_keybinds_to_toml(data), encoding="utf-8")
        logger.info(f"Migrated keybinds.json -> keybinds.toml at: {toml_path}")
        return True
    except Exception as e:
        logger.warning(f"Failed migrating {json_path} -> {toml_path}: {e}")
        return False


def ensure_default_keybinds_file(path: Path) -> None:
    """Create the keybinds config file with repo defaults if it doesn't exist."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            if _migrate_json_to_toml_if_present(path):
                return

            repo_default = _repo_default_keybinds_path()
            if repo_default.exists():
                path.write_text(repo_default.read_text(encoding="utf-8"), encoding="utf-8")
                logger.info(f"Copied default keybinds config to: {path}")
            else:
                logger.warning(
                    f"Repo default keybinds file missing at {repo_default}; leaving {path} uncreated."
                )
    except Exception as e:
        logger.warning(f"Failed to create default keybinds config at {path}: {e}")


def _validate_keybinds_shape(data: object) -> dict[str, dict[str, str]]:
    """
    Ensure the config data is a context->(key->action) mapping of strings.
    Invalid entries are ignored.
    """
    if not isinstance(data, Mapping):
        return {}

    out: dict[str, dict[str, str]] = {}
    for ctx, mapping in data.items():
        if not isinstance(ctx, str) or not isinstance(mapping, Mapping):
            continue
        ctx_map: dict[str, str] = {}
        for key, action in mapping.items():
            if isinstance(key, str) and isinstance(action, str):
                ctx_map[key] = action
        if ctx_map:
            out[ctx] = ctx_map

    return out


def load_keybinds_config() -> dict[str, dict[str, str]]:
    """
    Ensure a default keybinds file exists and load it.
    Returns {} on any error (app will use built-in defaults).
    """
    path = get_keybinds_path()
    ensure_default_keybinds_file(path)

    try:
        if tomllib is None:  # pragma: no cover
            logger.warning("tomllib is not available; cannot read TOML keybinds config.")
            return {}

        raw = tomllib.loads(path.read_text(encoding="utf-8"))
        return _validate_keybinds_shape(raw)
    except FileNotFoundError:
        return {}
    except Exception as e:
        logger.warning(f"Failed to load keybinds config from {path}: {e}")
        return {}
