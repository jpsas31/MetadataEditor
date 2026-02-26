from pathlib import Path

from src.keybindsConfig import (
    _is_valid_toml_key,
    _keybinds_to_toml,
    _toml_quote_key,
    _toml_quote_value,
    _validate_keybinds_shape,
    get_config_dir,
    get_keybinds_path,
)


class TestIsValidTomlKey:
    def test_valid_simple_keys(self):
        assert _is_valid_toml_key("global") is True
        assert _is_valid_toml_key("list") is True
        assert _is_valid_toml_key("editor") is True

    def test_valid_with_underscore_hyphen(self):
        assert _is_valid_toml_key("my_key") is True
        assert _is_valid_toml_key("my-key") is True
        assert _is_valid_toml_key("key123") is True

    def test_invalid_with_spaces(self):
        assert _is_valid_toml_key("my key") is False
        assert _is_valid_toml_key("global list") is False

    def test_invalid_with_dots(self):
        assert _is_valid_toml_key("my.key") is False
        assert _is_valid_toml_key("[global]") is False

    def test_empty_string(self):
        assert _is_valid_toml_key("") is False


class TestTomlQuoteKey:
    def test_simple_key_unchanged(self):
        assert _toml_quote_key("global") == "global"
        assert _toml_quote_key("list") == "list"

    def test_key_with_special_chars_quoted(self):
        assert _toml_quote_key("my key") == '"my key"'
        assert _toml_quote_key("key.with.dots") == '"key.with.dots"'

    def test_key_with_quotes_escaped(self):
        assert _toml_quote_key('key"with"quotes') == '"key\\"with\\"quotes"'

    def test_key_with_backslash_escaped(self):
        assert _toml_quote_key("key\\with\\backslash") == '"key\\\\with\\\\backslash"'


class TestTomlQuoteValue:
    def test_simple_value_unchanged(self):
        assert _toml_quote_value("quit") == '"quit"'
        assert _toml_quote_value("play") == '"play"'

    def test_value_with_quotes_escaped(self):
        assert _toml_quote_value('say "hello"') == '"say \\"hello\\""'

    def test_value_with_backslash_escaped(self):
        assert _toml_quote_value("path\\to\\file") == '"path\\\\to\\\\file"'


class TestKeybindsToToml:
    def test_empty_dict(self):
        result = _keybinds_to_toml({})
        assert "# MetadataEditor keybinds" in result
        assert result.endswith("\n")

    def test_single_context(self):
        data = {"global": {"q": "quit"}}
        result = _keybinds_to_toml(data)
        assert "[global]" in result
        assert 'q = "quit"' in result

    def test_multiple_contexts(self):
        data = {
            "global": {"q": "quit"},
            "list": {"j": "down", "k": "up"},
        }
        result = _keybinds_to_toml(data)
        assert "[global]" in result
        assert "[list]" in result
        assert 'j = "down"' in result
        assert 'k = "up"' in result


class TestValidateKeybindsShape:
    def test_valid_simple_mapping(self):
        data = {"global": {"q": "quit"}}
        result = _validate_keybinds_shape(data)
        assert result == {"global": {"q": "quit"}}

    def test_valid_multiple_contexts(self):
        data = {
            "global": {"q": "quit"},
            "list": {"j": "down", "k": "up"},
        }
        result = _validate_keybinds_shape(data)
        assert result == data

    def test_invalid_ctx_type_ignored(self):
        data = {123: {"q": "quit"}}
        result = _validate_keybinds_shape(data)
        assert result == {}

    def test_invalid_mapping_type_ignored(self):
        data = {"global": "not a mapping"}
        result = _validate_keybinds_shape(data)
        assert result == {}

    def test_invalid_key_type_ignored(self):
        data = {"global": {1: "quit"}}
        result = _validate_keybinds_shape(data)
        assert result == {}

    def test_invalid_action_type_ignored(self):
        data = {"global": {"q": 123}}
        result = _validate_keybinds_shape(data)
        assert result == {}

    def test_non_dict_input(self):
        assert _validate_keybinds_shape("string") == {}
        assert _validate_keybinds_shape([1, 2, 3]) == {}
        assert _validate_keybinds_shape(None) == {}

    def test_empty_mapping_ignored(self):
        data = {"global": {}, "list": {"k": "up"}}
        result = _validate_keybinds_shape(data)
        assert result == {"list": {"k": "up"}}


class TestGetConfigDir:
    def test_default_xdg(self, monkeypatch):
        monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
        result = get_config_dir()
        assert result == Path.home() / ".config" / "metadataEditor"

    def test_xdg_config_home_used(self, monkeypatch):
        monkeypatch.setenv("XDG_CONFIG_HOME", "/custom/config")
        result = get_config_dir()
        assert result == Path("/custom/config/metadataEditor")


class TestGetKeybindsPath:
    def test_returns_config_dir_keybinds_toml(self, monkeypatch):
        monkeypatch.setenv("XDG_CONFIG_HOME", "/test/config")
        result = get_keybinds_path()
        assert result == Path("/test/config/metadataEditor/keybinds.toml")
