import logging
import re
from typing import Hashable, Literal

import urwid

from ansiParser import ansi_attr_parser, ansi_text_parser

logging.basicConfig(
    filename="/tmp/album_art_debug.log",
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filemode="w",
)
logger = logging.getLogger(__name__)


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
        logger.info(f"Setting text to: {text}")
        if len(text) == 0:
            super().set_text(text)
            return

        attr_list = ansi_attr_parser(text)
        if len(attr_list) == 0:
            super().set_text(text)
            return

        ansi_text = ansi_text_parser(text, attr_list)
        markup = self.ansi_markup_parser(ansi_text)
        super().set_text(markup)

    def ansi_markup_parser(self, ansi_markup: list[tuple[str, str]]) -> list[tuple[str, str]]:
        markup = []
        for c in ansi_markup:
            fg = c[0][0] if c[0][0] is not None else "default"
            bg = c[0][1] if c[0][1] is not None else "default"

            markup.append((urwid.AttrSpec(fg, bg, 16777216), c[1]))
        return markup


def main():
    texts = [
        "Removing cache dir /Users/jpsalgado@truora.com/.cache/yt-dlp .",
        "[download] [0;94m  0.5%[0m of  187.05KiB at [0;32m Unknown B/s[0m ETA [0;33mUnknown[0m",
        "[download] [0;94m  1.6%[0m of  187.05KiB at [0;32m   2.47MiB/s[0m ETA [0;33m00:00[0m",
        "[download] [0;94m  3.7%[0m of  187.05KiB at [0;32m   4.18MiB/s[0m ETA [0;33m00:00[0m",
        "[download] [0;94m  8.0%[0m of  187.05KiB at [0;32m   7.22MiB/s[0m ETA [0;33m00:00[0m",
        "[download] [0;94m 16.6%[0m of  187.05KiB at [0;32m   6.80MiB/s[0m ETA [0;33m00:00[0m",
        "[download] [0;94m 33.7%[0m of  187.05KiB at [0;32m   3.54MiB/s[0m ETA [0;33m00:00[0m",
        "[download] [0;94m 67.9%[0m of  187.05KiB at [0;32m   4.34MiB/s[0m ETA [0;33m00:00[0m",
        "[download] [0;94m100.0%[0m of  187.05KiB at [0;32m   4.73MiB/s[0m ETA [0;33m00:00[0m",
        "[download] 100% of  187.05KiB in [1;37m00:00:00[0m at [0;32m646.97KiB/s[0m",
        "",
        "\x1b[0mNormal \x1b[1mBold \x1b[3mItalic \x1b[4mUnderline \x1b[5mBlink \x1b[7mReversed\x1b[0m",
        "\x1b[31mRed \x1b[32mGreen \x1b[34mBlue \x1b[36mCyan \x1b[0m",
        "\x1b[41mRed BG \x1b[42mGreen BG \x1b[44mBlue BG \x1b[0m",
        "\x1b[1;33;44mBold Yellow on Blue\x1b[0m",
        "\x1b[48;2;0;0;0;38;2;255;100;0m Orange text on Black \x1b[0m",
        "\x1b[1;3;4;38;5;214;48;2;90;0;0m Bold, Italic, Underline, Orange FG, Deep Red BG \x1b[0m",
    ]

    pile_contents = [ANSIText(t) for t in texts]
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
    main()
    main()
    main()
    main()
