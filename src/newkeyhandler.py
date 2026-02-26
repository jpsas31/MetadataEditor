from collections.abc import Callable, Mapping
from typing import Any

import urwid

from src.logging_config import setup_logging

logger = setup_logging(__name__)

# Context IDs (used to scope key bindings)
CTX_GLOBAL = "global"
CTX_LIST = "list"
CTX_METADATA = "metadata"
CTX_YOUTUBE = "youtube"
CTX_POPUP = "popup"


class KeyBinding:
    """Represents a keyboard shortcut binding with context support."""

    def __init__(
        self,
        key: str,
        description: str,
        action: Callable,
        global_key: bool = False,
        needs_context: bool = False,
    ):
        self.key = key
        self.description = description
        self.action = action
        self.global_key = global_key
        self.needs_context = needs_context

    def __repr__(self):
        scope = "Global" if self.global_key else "Local"
        context = " (context-aware)" if self.needs_context else ""
        return f"KeyBinding('{self.key}', '{self.description}', {scope}{context})"


class KeyHandler:
    """Context-aware keyboard shortcut management system."""

    def __init__(self, config: Mapping[str, Mapping[str, str]] | None = None):
        self.actions: dict[str, Callable] = {}
        self.keymaps: dict[str, dict[str, str]] = {}
        self.config = config or {}
        self.list_widget = None
        self.context_parents: dict[str, str] = {
            CTX_LIST: CTX_GLOBAL,
            CTX_METADATA: CTX_GLOBAL,
            CTX_YOUTUBE: CTX_GLOBAL,
            CTX_POPUP: CTX_GLOBAL,
        }
        self._initialize_default_mappings()

    def get_context_chain(self, widget_context: str) -> list[str]:
        """
        Return the fallback chain for a context, ending in CTX_GLOBAL.

        Example: "list" -> ["list", "global"]
        """
        context = widget_context or CTX_GLOBAL
        chain: list[str] = []
        seen: set[str] = set()

        while context and context not in seen:
            chain.append(context)
            seen.add(context)
            context = self.context_parents.get(context)

        if CTX_GLOBAL not in chain:
            chain.append(CTX_GLOBAL)

        return chain

    def _apply_keymap_config(self, config: Mapping[str, Mapping[str, str]]) -> None:
        """
        Apply key mapping config.

        Shape: {"global": {...}, "list": {...}, "metadata": {...}}
        """
        if not all(
            isinstance(ctx, str) and isinstance(mapping, Mapping) for ctx, mapping in config.items()
        ):
            raise ValueError(
                "KeyHandler config must be context-based: "
                "{'global': {..}, 'list': {..}, 'metadata': {..}, ...}"
            )

        for ctx, mapping in config.items():
            if ctx not in self.keymaps:
                logger.warning(f"Ignoring unknown keymap context '{ctx}'")
                continue
            for key, action in mapping.items():
                if isinstance(key, str) and isinstance(action, str):
                    self.keymaps[ctx][key] = action
                else:
                    logger.warning(
                        f"Ignoring invalid mapping in context '{ctx}': {key!r} -> {action!r}"
                    )

    def _initialize_default_mappings(self):
        """Initialize default key mappings."""
        default_global = {
            "esc": "app_exit",
            "F1": "show_help",
            "1": "view_switch_0",
            "2": "view_switch_1",
            "3": "view_switch_2",
        }

        default_list = {
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
            "delete": "delete",
        }

        self.keymaps = {
            CTX_GLOBAL: {},
            CTX_LIST: {},
            CTX_METADATA: {},
            CTX_YOUTUBE: {},
            CTX_POPUP: {},
        }

        self.keymaps[CTX_GLOBAL].update(default_global)
        self.keymaps[CTX_LIST].update(default_list)

        if isinstance(self.config, Mapping) and self.config:
            self._apply_keymap_config(self.config)

    def register_action(self, action_name: str, handler: Callable, needs_context: bool = False):
        """
        Register an action handler.

        Args:
            action_name: The name of the action (e.g., "nav_up", "playback_toggle")
            handler: The callable to execute when this action is triggered
            needs_context: If True, handler will receive context dict as first argument
        """
        if not callable(handler):
            raise ValueError(f"Handler for action '{action_name}' must be callable.")

        self.actions[action_name] = {
            "handler": handler,
            "needs_context": needs_context,
        }

    def handle_key(
        self,
        key: str,
        widget_context: str = CTX_GLOBAL,
        context: dict[str, Any] | None = None,
    ) -> bool:
        """
        Handle a key press with context awareness.

        Args:
            key: The key that was pressed
            widget_context: The context/widget where key was pressed (e.g., "list", "metadata")
            context: Optional context dict with dynamic data like cursor_pos, widget, etc.

        Returns:
            True if key was handled, False otherwise
        """
        if not isinstance(key, str) or not key:
            return False

        action_name = None
        for ctx in self.get_context_chain(widget_context):
            action_name = self.keymaps.get(ctx, {}).get(key)
            if action_name:
                break

        if not action_name:
            return False

        if action_name not in self.actions:
            return False

        action_info = self.actions[action_name]
        handler = action_info["handler"]
        needs_context = action_info.get("needs_context", False)

        try:
            if needs_context:
                if context is None:
                    context = self._get_default_context()
                handler(context)
            else:
                handler()
            return True
        except urwid.ExitMainLoop:
            raise
        except Exception as e:
            logger.error(f"Error handling key '{key}' (action '{action_name}'): {e}")
            return False

    def _get_default_context(self) -> dict[str, Any]:
        """Get default context when none is provided."""
        context = {}

        if self.list_widget:
            try:
                focus_widget, cursor_pos = self.list_widget.get_focus()
                context["cursor_pos"] = cursor_pos
                context["widget"] = self.list_widget
                context["focus_widget"] = focus_widget
            except Exception:
                pass

        return context

    def add_key_mapping(self, key: str, action: str, context: str = CTX_LIST):
        """Add a new key mapping to a specific context."""
        self.keymaps.setdefault(context, {})[key] = action

    def remove_key_mapping(self, key: str):
        """Remove a key mapping."""
        for ctx_map in self.keymaps.values():
            if key in ctx_map:
                del ctx_map[key]

    def dump_bindings(self, context: str | None = None) -> dict[str, Any]:
        """
        Return a structured representation of keymaps and registrations for debugging.

        Args:
            context: If provided, only include that context.
        """
        contexts = [context] if context else list(self.keymaps.keys())
        dump: dict[str, Any] = {
            "contexts": {},
            "context_parents": dict(self.context_parents),
            "registered_actions": sorted(self.actions.keys()),
        }

        for ctx in contexts:
            ctx_map = self.keymaps.get(ctx, {})
            dump["contexts"][ctx] = {
                "keys": dict(sorted(ctx_map.items())),
                "fallback_chain": self.get_context_chain(ctx),
            }

        return dump

    def get_help_text(self, context: str | None = None) -> str:
        """
        Get formatted help text showing shortcuts.

        Args:
            context: If provided, show shortcuts resolvable from that context
                     (context + fallbacks). If None, show global + list.
        """
        help_lines = ["Keyboard Shortcuts:", ""]

        if context:
            chain = self.get_context_chain(context)
            for ctx in chain:
                ctx_map = self.keymaps.get(ctx, {})
                if not ctx_map:
                    continue
                label = (
                    "Global (work from any widget):"
                    if ctx == CTX_GLOBAL
                    else f"{ctx.title()} keys:"
                )
                help_lines.append(label)
                for key, action in sorted(ctx_map.items()):
                    if action in self.actions:
                        help_lines.append(f"  {key:15} - {action}")
                help_lines.append("")
            return "\n".join(help_lines).rstrip()

        # Default output: global + list.
        global_shortcuts = self.keymaps.get(CTX_GLOBAL, {})
        list_shortcuts = self.keymaps.get(CTX_LIST, {})

        if global_shortcuts:
            help_lines.append("Global (work from any widget):")
            for key, action in sorted(global_shortcuts.items()):
                if action in self.actions:
                    help_lines.append(f"  {key:15} - {action}")
            help_lines.append("")

        if list_shortcuts:
            help_lines.append("List keys:")
            for key, action in sorted(list_shortcuts.items()):
                if action in self.actions:
                    help_lines.append(f"  {key:15} - {action}")

        return "\n".join(help_lines)
