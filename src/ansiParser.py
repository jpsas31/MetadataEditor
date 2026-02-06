import re

# ansi has the sequence style->foreground color->background color
# special case when use 256 color mode
# style-> 38 -> 5 -> {ID}m	Set foreground color where {ID} is a number between 0 and 255.
# style-> 48 -> 5 -> {ID}m	Set background color where {ID} is a number between 0 and 255.

ANSI_ESCAPE_PATTERN = re.compile(r"(\x1b\[[0-9;]*[a-zA-Z])")
ANSI_SYMBOL = "\x1b"

ANSI_ESCAPE_CODES_REVERSE = 20
SEPARATOR = ", "
ANSI_ESCAPE_CODES = {
    1: "bold",  # to return to normal use 22
    3: "italics",  # to return to normal add ANSI_ESCAPE_CODES_REVERSE
    4: "underline",
    5: "blink",  # to return to normal add ANSI_ESCAPE_CODES_REVERSE
    7: "standout",  # to return to normal add ANSI_ESCAPE_CODES_REVERSE
    9: "strikethrough",  # to return to normal add ANSI_ESCAPE_CODES_REVERSE
}


URWID_COLOR_CODES = {
    # Standard Colors (0-7)
    0: "black",
    1: "dark red",
    2: "dark green",
    3: "brown",  # ANSI Yellow (Low Intensity)
    4: "dark blue",
    5: "dark magenta",
    6: "dark cyan",
    7: "light gray",  # ANSI White (Low Intensity)
    # High Intensity / "Light" Colors (8-15)
    8: "dark gray",  # ANSI Black (High Intensity)
    9: "light red",
    10: "light green",
    11: "yellow",  # ANSI Yellow (High Intensity)
    12: "light blue",
    13: "light magenta",
    14: "light cyan",
    15: "white",  # ANSI White (High Intensity)
}


def debug_ansi_sequences(text: str) -> None:
    """Print each ANSI sequence and the text that follows as one repr (sequence + text)."""
    parts = re.split(ANSI_ESCAPE_PATTERN, text)
    for i, part in enumerate(parts):
        if not part:
            continue
        if part.startswith(ANSI_SYMBOL):
            next_text = parts[i + 1] if i + 1 < len(parts) else ""
            combined = part + next_text
            s = repr(combined)
            if len(s) > 120:
                s = repr(combined[:80] + "...") + "  (truncated)"
            print(f"  {s}")
        else:
            if i == 0 and part.strip():
                s = repr(part[:80]) + ("..." if len(part) > 80 else "")
                print(f"  (no sequence) {s}")


def get_urwid_color_code(ansi_color_code: int) -> str:
    base_color = ansi_color_code % 10
    if ansi_color_code >= 90:
        base_color += 8
    return URWID_COLOR_CODES[base_color]


def rgb_to_hex(rgb_tuple):
    return f"#{rgb_tuple[0]:02X}{rgb_tuple[1]:02X}{rgb_tuple[2]:02X}"


def ansi_attr_parser(text: str) -> list[tuple[str, str]]:
    matches = []
    attr_list = []
    matches = re.split(ANSI_ESCAPE_PATTERN, text)

    if len(matches) == 0:
        return [((None, None), text)]

    is_foreground = False
    is_background = False
    is_rgb = False
    rgb_values = []
    is_256 = False
    attr_spec_fg = []
    attr_spec_bg = []
    is_previous_ansi_code = False

    for text in matches:
        vals = []
        if len(text) == 0:
            continue

        if not text.startswith(ANSI_SYMBOL):
            if not is_previous_ansi_code:
                attr_list.append(((None, None), text))
                continue
            else:
                attr_list.append(
                    ((SEPARATOR.join(attr_spec_fg), SEPARATOR.join(attr_spec_bg)), text)
                )
                is_previous_ansi_code = False
                attr_spec_fg = []
                attr_spec_bg = []
                continue

        vals = text[2:-1].split(";")
        if not vals:
            vals = ["0"]

        for val in vals:
            val_int = int(val)

            if is_rgb:
                rgb_values.append(val_int)
                if len(rgb_values) == 3:
                    is_rgb = False
                    if is_foreground:
                        is_foreground = False
                        attr_spec_fg.append(rgb_to_hex(rgb_values))

                    if is_background:
                        is_background = False
                        attr_spec_bg.append(rgb_to_hex(rgb_values))

                    rgb_values = []
                continue

            if is_256:
                if is_foreground:
                    is_foreground = False
                    is_256 = False
                    attr_spec_fg.append(f"h{val}")
                if is_background:
                    is_background = False
                    is_256 = False
                    attr_spec_bg.append(f"h{val}")

                continue

            if val_int == 0:
                continue

            if val_int == 38:
                is_foreground = True
                continue

            if val_int == 48:
                is_background = True
                continue

            if (is_background or is_foreground) and val_int == 2:
                is_rgb = True
                continue

            if (is_background or is_foreground) and val_int == 5:
                is_256 = True
                continue

            if val_int in ANSI_ESCAPE_CODES:
                attr_spec_fg.append(ANSI_ESCAPE_CODES[val_int])
                continue

            if 30 <= val_int < 38 or 90 <= val_int <= 97:  # Standard Foreground colors.
                attr_spec_fg.append(get_urwid_color_code(val_int))
                continue

            if 40 <= val_int < 48 or 100 <= val_int <= 107:
                # Standard Background colors.
                attr_spec_bg.append(get_urwid_color_code(val_int))
                continue

        is_previous_ansi_code = True

    return attr_list


def _test_parse_album_art_from_cache():
    """Read one album art from AlbumArtCache and parse with ansi_attr_parser."""
    import pickle

    try:
        from albumArtCache import AlbumArtCache
    except ImportError:
        from src.albumArtCache import AlbumArtCache

    cache = AlbumArtCache()
    album_art_size = (80, 40)
    # Try to get one from disk, or seed and get
    pkl_files = list(cache.cache_dir.glob("*.pkl"))
    if not pkl_files:
        sample_ascii = "\x1b[31m#\x1b[0m\x1b[32m@\x1b[0m"
        cache.set("__test_album_art__", b"dummy", sample_ascii, album_art_size)
        ascii_art = cache.get("__test_album_art__", b"dummy", album_art_size)
    else:
        with open(pkl_files[0], "rb") as f:
            ascii_art = pickle.load(f)
    if ascii_art is None:
        print("ansiParser cache test: no album art from cache, skip")
        return
    try:
        print(ascii_art)
        debug_ansi_sequences(ascii_art)
        parsed = ansi_attr_parser(ascii_art)
        print(f"ansiParser cache test: parsed {len(parsed)} segments")
        print(parsed)
    except Exception as e:
        print(f"ansiParser cache test FAILED: {e}")
        raise


def main():
    # _test_parse_album_art_from_cache()

    texts = [
        "\x1b[4mUnderline \x1b[5mBlink \x1b[7mReversed\x1b[0m\n\x1b[31mRed \x1b[32mGreen",
        # "Removing cache dir /Users/jpsalgado@truora.com/.cache/yt-dlp .",
        # "[download] [0;94m  0.5%[0m of  187.05KiB at [0;32m Unknown B/s[0m ETA [0;33mUnknown[0m",
        # "",
        # "\x1b[0mNormal \x1b[1mBold \x1b[3mItalic \x1b[4mUnderline \x1b[5mBlink \x1b[7mReversed\x1b[0m",
        # "\x1b[31mRed \x1b[32mGreen \x1b[34mBlue \x1b[36mCyan \x1b[0m",
        # "\x1b[41mRed BG \x1b[42mGreen BG \x1b[44mBlue BG \x1b[0m",
        # "\x1b[38;2;255;0;0m▄ \x1b[38;2;0;255;0m▄ \x1b[38;2;0;0;255m▄\x1b[0m",
        # "\x1b[1;33;44mBold Yellow on Blue\x1b[0m",
        # "\x1b[48;2;0;0;0;38;2;255;100;0m Orange text on Black \x1b[0m",
        # "\x1b[1;3;4;38;5;214;48;2;90;0;0m Bold, Italic, Underline, Orange FG, Deep Red BG \x1b[0m",
        # "\x1b[48;5;243m\x1b[38;5;237m▄",
    ]

    for t in texts:
        # debug_ansi_sequences(t)  # uncomment to print raw ANSI codes instead of colors
        attr_list = ansi_attr_parser(t)
        print(attr_list)
        # ansi_text = ansi_text_parser(t, attr_list)
        # print(ansi_text)


if __name__ == "__main__":
    main()
