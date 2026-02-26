from src.ansiParser import (
    ansi_attr_parser,
    get_urwid_color_code,
    rgb_to_hex,
)


class TestRgbToHex:
    def test_black(self):
        assert rgb_to_hex((0, 0, 0)) == "#000000"

    def test_white(self):
        assert rgb_to_hex((255, 255, 255)) == "#FFFFFF"

    def test_red(self):
        assert rgb_to_hex((255, 0, 0)) == "#FF0000"

    def test_green(self):
        assert rgb_to_hex((0, 255, 0)) == "#00FF00"

    def test_blue(self):
        assert rgb_to_hex((0, 0, 255)) == "#0000FF"

    def test_mixed(self):
        assert rgb_to_hex((128, 64, 32)) == "#804020"


class TestGetUrwidColorCode:
    def test_standard_colors_0_7(self):
        assert get_urwid_color_code(30) == "black"
        assert get_urwid_color_code(31) == "dark red"
        assert get_urwid_color_code(32) == "dark green"
        assert get_urwid_color_code(33) == "brown"
        assert get_urwid_color_code(34) == "dark blue"
        assert get_urwid_color_code(35) == "dark magenta"
        assert get_urwid_color_code(36) == "dark cyan"
        assert get_urwid_color_code(37) == "light gray"

    def test_high_intensity_90_97(self):
        assert get_urwid_color_code(90) == "dark gray"
        assert get_urwid_color_code(91) == "light red"
        assert get_urwid_color_code(92) == "light green"
        assert get_urwid_color_code(93) == "yellow"
        assert get_urwid_color_code(94) == "light blue"
        assert get_urwid_color_code(95) == "light magenta"
        assert get_urwid_color_code(96) == "light cyan"
        assert get_urwid_color_code(97) == "white"


class TestAnsiAttrParser:
    def test_plain_text(self):
        result = ansi_attr_parser("Hello World")
        assert result == [((None, None), "Hello World")]

    def test_empty_string(self):
        result = ansi_attr_parser("")
        assert result == []

    def test_bold(self):
        result = ansi_attr_parser("\x1b[1mBold\x1b[0m")
        assert len(result) == 1
        assert result[0][0][0] == "bold"
        assert result[0][1] == "Bold"

    def test_italic(self):
        result = ansi_attr_parser("\x1b[3mItalic\x1b[0m")
        assert result[0][0][0] == "italics"
        assert result[0][1] == "Italic"

    def test_underline(self):
        result = ansi_attr_parser("\x1b[4mUnderline\x1b[0m")
        assert result[0][0][0] == "underline"
        assert result[0][1] == "Underline"

    def test_foreground_color(self):
        result = ansi_attr_parser("\x1b[31mRed Text\x1b[0m")
        assert "dark red" in result[0][0][0]
        assert result[0][1] == "Red Text"

    def test_background_color(self):
        result = ansi_attr_parser("\x1b[41mRed BG\x1b[0m")
        assert "dark red" in result[0][0][1]
        assert result[0][1] == "Red BG"

    def test_multiple_attributes(self):
        result = ansi_attr_parser("\x1b[1;31mBold Red\x1b[0m")
        assert "bold" in result[0][0][0]
        assert "dark red" in result[0][0][0]

    def test_rgb_foreground(self):
        result = ansi_attr_parser("\x1b[38;2;255;0;0mRed RGB\x1b[0m")
        assert "#FF0000" in result[0][0][0]
        assert result[0][1] == "Red RGB"

    def test_rgb_background(self):
        result = ansi_attr_parser("\x1b[48;2;0;255;0mGreen BG\x1b[0m")
        assert "#00FF00" in result[0][0][1]
        assert result[0][1] == "Green BG"

    def test_256_color_foreground(self):
        result = ansi_attr_parser("\x1b[38;5;214mOrange\x1b[0m")
        assert "h214" in result[0][0][0]

    def test_256_color_background(self):
        result = ansi_attr_parser("\x1b[48;5;243m256 BG\x1b[0m")
        assert "h243" in result[0][0][1]

    def test_mixed_text_and_ansi(self):
        result = ansi_attr_parser("Normal \x1b[1mBold\x1b[0m Normal")
        assert result[0][1] == "Normal "
        assert result[1][0][0] == "bold"
        assert result[1][1] == "Bold"
        assert result[2][1] == " Normal"

    def test_reset_code_only(self):
        result = ansi_attr_parser("\x1b[0m")
        assert result == []

    def test_blink(self):
        result = ansi_attr_parser("\x1b[5mBlink\x1b[0m")
        assert result[0][0][0] == "blink"

    def test_standout(self):
        result = ansi_attr_parser("\x1b[7mStandout\x1b[0m")
        assert result[0][0][0] == "standout"

    def test_strikethrough(self):
        result = ansi_attr_parser("\x1b[9mStrikethrough\x1b[0m")
        assert result[0][0][0] == "strikethrough"
