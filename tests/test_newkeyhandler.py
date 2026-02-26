import pytest

from src.newkeyhandler import (
    CTX_GLOBAL,
    CTX_LIST,
    CTX_METADATA,
    CTX_POPUP,
    CTX_YOUTUBE,
    KeyBinding,
    KeyHandler,
)


class TestKeyBinding:
    def test_creation(self):
        binding = KeyBinding("q", "Quit", lambda: None)
        assert binding.key == "q"
        assert binding.description == "Quit"
        assert binding.global_key is False
        assert binding.needs_context is False

    def test_repr_global(self):
        binding = KeyBinding("q", "Quit", lambda: None, global_key=True)
        assert "Global" in repr(binding)

    def test_repr_local(self):
        binding = KeyBinding("j", "Down", lambda: None, global_key=False)
        assert "Local" in repr(binding)

    def test_repr_context_aware(self):
        binding = KeyBinding("j", "Down", lambda: None, needs_context=True)
        assert "context-aware" in repr(binding)


class TestKeyHandlerContextChain:
    def test_global_chain(self):
        handler = KeyHandler()
        chain = handler.get_context_chain(CTX_GLOBAL)
        assert chain == [CTX_GLOBAL]

    def test_list_chain(self):
        handler = KeyHandler()
        chain = handler.get_context_chain(CTX_LIST)
        assert chain == [CTX_LIST, CTX_GLOBAL]

    def test_metadata_chain(self):
        handler = KeyHandler()
        chain = handler.get_context_chain(CTX_METADATA)
        assert chain == [CTX_METADATA, CTX_GLOBAL]

    def test_youtube_chain(self):
        handler = KeyHandler()
        chain = handler.get_context_chain(CTX_YOUTUBE)
        assert chain == [CTX_YOUTUBE, CTX_GLOBAL]

    def test_popup_chain(self):
        handler = KeyHandler()
        chain = handler.get_context_chain(CTX_POPUP)
        assert chain == [CTX_POPUP, CTX_GLOBAL]

    def test_none_context_defaults_to_global(self):
        handler = KeyHandler()
        chain = handler.get_context_chain(None)
        assert chain == [CTX_GLOBAL]


class TestKeyHandlerRegisterAction:
    def test_register_simple_action(self):
        handler = KeyHandler()
        handler.register_action("quit", lambda: None)
        assert "quit" in handler.actions

    def test_register_action_with_context(self):
        handler = KeyHandler()
        handler.register_action("nav_up", lambda: None, needs_context=True)
        assert "nav_up" in handler.actions
        assert handler.actions["nav_up"]["needs_context"] is True

    def test_register_invalid_raises(self):
        handler = KeyHandler()
        with pytest.raises(ValueError):
            handler.register_action("quit", "not_callable")


class TestKeyHandlerApplyConfig:
    def test_apply_valid_config(self):
        handler = KeyHandler()
        config = {
            "global": {"q": "quit"},
            "list": {"j": "nav_down"},
        }
        handler._apply_keymap_config(config)
        assert handler.keymaps[CTX_GLOBAL]["q"] == "quit"
        assert handler.keymaps[CTX_LIST]["j"] == "nav_down"

    def test_apply_invalid_config_raises(self):
        handler = KeyHandler()
        with pytest.raises((ValueError, AttributeError)):
            handler._apply_keymap_config("not a dict")

    def test_apply_invalid_context_ignored(self):
        handler = KeyHandler()
        config = {"invalid_ctx": {"q": "quit"}}
        handler._apply_keymap_config(config)
        assert "invalid_ctx" not in handler.keymaps


class TestKeyHandlerHandleKey:
    def test_handle_unknown_key_returns_false(self):
        handler = KeyHandler()
        handler.register_action("quit", lambda: None)
        result = handler.handle_key("unknown_key")
        assert result is False

    def test_handle_unregistered_action_returns_false(self):
        handler = KeyHandler()
        handler.keymaps[CTX_GLOBAL]["q"] = "quit"
        result = handler.handle_key("q")
        assert result is False

    def test_handle_valid_key_returns_true(self):
        handler = KeyHandler()
        handler.register_action("quit", lambda: None)
        handler.keymaps[CTX_GLOBAL]["q"] = "quit"
        result = handler.handle_key("q")
        assert result is True

    def test_handle_invalid_key_type_returns_false(self):
        handler = KeyHandler()
        result = handler.handle_key(123)
        assert result is False

    def test_handle_empty_key_returns_false(self):
        handler = KeyHandler()
        result = handler.handle_key("")
        assert result is False


class TestKeyHandlerKeyMapping:
    def test_add_key_mapping(self):
        handler = KeyHandler()
        handler.add_key_mapping("q", "quit", CTX_LIST)
        assert handler.keymaps[CTX_LIST]["q"] == "quit"

    def test_remove_key_mapping(self):
        handler = KeyHandler()
        handler.keymaps[CTX_GLOBAL]["q"] = "quit"
        handler.remove_key_mapping("q")
        assert "q" not in handler.keymaps[CTX_GLOBAL]


class TestKeyHandlerDumpBindings:
    def test_dump_all_contexts(self):
        handler = KeyHandler()
        handler.register_action("quit", lambda: None)
        dump = handler.dump_bindings()
        assert "contexts" in dump
        assert CTX_GLOBAL in dump["contexts"]
        assert CTX_LIST in dump["contexts"]

    def test_dump_specific_context(self):
        handler = KeyHandler()
        dump = handler.dump_bindings(CTX_LIST)
        assert CTX_LIST in dump["contexts"]
        assert CTX_GLOBAL not in dump["contexts"] or CTX_GLOBAL in dump["contexts"]


class TestKeyHandlerHelpText:
    def test_help_text_with_registered_actions(self):
        handler = KeyHandler()
        handler.register_action("quit", lambda: None)
        handler.keymaps[CTX_GLOBAL]["q"] = "quit"
        help_text = handler.get_help_text()
        assert "Keyboard Shortcuts" in help_text

    def test_help_text_specific_context(self):
        handler = KeyHandler()
        handler.register_action("nav_up", lambda: None)
        handler.keymaps[CTX_LIST]["j"] = "nav_up"
        help_text = handler.get_help_text(CTX_LIST)
        assert "j" in help_text
        assert "nav_up" in help_text
