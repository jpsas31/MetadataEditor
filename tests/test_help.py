from src.urwid_components.help import HelpDialog


class TestHelpDialog:
    def test_scope_descriptions_class_attribute(self):
        assert HelpDialog.scope_descriptions["global"] == "Works anywhere"
        assert HelpDialog.scope_descriptions["list"] == "Works when focus is on the song list"

    def test_format_keybinds_config_single_scope(self):
        keybinds_config = {
            "global": {"q": "quit", "esc": "exit"},
        }
        dialog = HelpDialog(keybinds_config, lambda x: None)
        result = dialog.format_keybinds_config(keybinds_config)

        assert "Keybinds Configuration" in str(result)
        assert "GLOBAL" in str(result)
        assert "q" in str(result)
        assert "quit" in str(result)

    def test_format_keybinds_config_multiple_scopes(self):
        keybinds_config = {
            "global": {"q": "quit"},
            "list": {"j": "down", "k": "up"},
        }
        dialog = HelpDialog(keybinds_config, lambda x: None)
        result = dialog.format_keybinds_config(keybinds_config)

        result_str = str(result)
        assert "GLOBAL" in result_str
        assert "LIST" in result_str

    def test_format_keybinds_config_empty(self):
        keybinds_config = {}
        dialog = HelpDialog(keybinds_config, lambda x: None)
        result = dialog.format_keybinds_config(keybinds_config)

        assert "Keybinds Configuration" in str(result)
