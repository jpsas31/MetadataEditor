from collections.abc import Hashable
from typing import Literal

import urwid

from ansiParser import ansi_attr_parser


class ANSIText(urwid.Text):
    def __init__(
        self,
        markup: str | tuple[Hashable, str] | list[str | tuple[Hashable, str]],
        align: Literal["left", "center", "right"] | urwid.Align = urwid.Align.LEFT,
        wrap: Literal["space", "any", "clip", "ellipsis"] | urwid.WrapMode = urwid.WrapMode.SPACE,
        layout: urwid.text_layout.TextLayout | None = None,
    ) -> None:
        super().__init__(markup, align, wrap, layout)

    def set_text(self, text: str):
        if len(text) == 0:
            super().set_text(text)
            return

        ansi_text = ansi_attr_parser(text)

        markup = self.ansi_markup_parser(ansi_text)
        super().set_text(markup)

    def ansi_markup_parser(self, ansi_markup: list[tuple[str, str]]) -> list[tuple[str, str]]:
        markup = []

        for c in ansi_markup:
            fg = c[0][0] if c[0][0] is not None and c[0][0] != "" else "default"
            bg = c[0][1] if c[0][1] is not None and c[0][1] != "" else "default"

            markup.append((urwid.AttrSpec(fg, bg, 16777216), c[1]))
        return markup


def _test_parse_album_art_from_cache():
    """Read one album art from AlbumArtCache and parse with ANSIText.set_text."""
    import pickle
    from pathlib import Path

    try:
        from albumArtCache import AlbumArtCache
    except ImportError:
        import sys

        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from albumArtCache import AlbumArtCache

    cache = AlbumArtCache()
    album_art_size = (80, 40)
    pkl_files = list(cache.cache_dir.glob("*.pkl"))
    if not pkl_files:
        sample_ascii = "\x1b[31m#\x1b[0m\x1b[32m@\x1b[0m"
        cache.set("__test_album_art__", b"dummy", sample_ascii, album_art_size)
        ascii_art = cache.get("__test_album_art__", b"dummy", album_art_size)
    else:
        with open(pkl_files[0], "rb") as f:
            ascii_art = pickle.load(f)
    if ascii_art is None:
        print("ansiText cache test: no album art from cache, skip")
        return
    try:
        widget = ANSIText(ascii_art)
        # widget.set_text(ascii_art)
        # cover_widget = ANSIWidget(ascii_art)

        centered_cover = urwid.Padding(widget, align="center", width="pack")

        new_linebox = urwid.Filler(centered_cover, valign="middle")

        return new_linebox
        print("ansiText cache test: set_text OK")
    except Exception as e:
        print(f"ansiText cache test FAILED: {e}")
        raise


def main():
    _test_parse_album_art_from_cache()

    texts = [
        "\x1b[0mNormal \x1b[1mBold \x1b[3mItalic \x1b[4mUnderline \x1b[5mBlink \x1b[7mReversed\x1b[0m\n\x1b[31mRed \x1b[32mGreen \x1b[34mBlue \x1b[36mCyan \x1b[0m\n\x1b[41mRed BG \x1b[42mGreen BG \x1b[44mBlue BG \x1b[0m\n\x1b[1;33;44mBold Yellow on Blue\x1b[0m\n\x1b[48;2;0;0;0;38;2;255;100;0m Orange text on Black \x1b[0m\n\x1b[1;3;4;38;5;214;48;2;90;0;0m Bold, Italic, Underline, Orange FG, Deep Red BG \x1b[0m",
        "\x1b[4mUnderline \x1b[5mBlink \x1b[7mReversed\x1b[0m\n\x1b[31mRed \x1b[32mGreen",
        "Removing cache dir /Users/jpsalgado@truora.com/.cache/yt-dlp .",
        "[download] [0;94m  0.5%[0m of  187.05KiB at [0;32m Unknown B/s[0m ETA [0;33mUnknown[0m",
        "",
        "\x1b[0mNormal \x1b[1mBold \x1b[3mItalic \x1b[4mUnderline \x1b[5mBlink \x1b[7mReversed\x1b[0m",
    ]

    pile_contents = [ANSIText(t) for t in texts]
    pile_contents.append(_test_parse_album_art_from_cache())
    pile = urwid.Pile(pile_contents)
    fill = urwid.Filler(pile, valign="top")

    screen = urwid.raw_display.Screen()

    def exit_on_q(key):
        if key in ("q", "Q"):
            raise urwid.ExitMainLoop()

    loop = urwid.MainLoop(fill, screen=screen, unhandled_input=exit_on_q)
    loop.run()


if __name__ == "__main__":
    main()
