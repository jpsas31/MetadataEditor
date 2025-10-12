import re
from typing import Any, Iterable, List, Optional, Tuple

import urwid


class ANSICanvas(urwid.canvas.Canvas):
    def __init__(self, size: Tuple[int, ...], text_lines: List[str]) -> None:
        super().__init__()

        if len(size) == 1:
            self.maxcols = size[0]
            self.maxrows = len(text_lines)
        else:
            self.maxcols, self.maxrows = size

        self.text_lines = text_lines

    def cols(self) -> int:
        return self.maxcols

    def rows(self) -> int:
        return self.maxrows

    def content(
        self,
        trim_left: int = 0,
        trim_top: int = 0,
        cols: Optional[int] = None,
        rows: Optional[int] = None,
        attr_map: Optional[Any] = None,
    ) -> Iterable[List[Tuple[None, str, bytes]]]:
        assert cols is not None
        assert rows is not None

        for i in range(rows):
            if i < len(self.text_lines):
                text = self.text_lines[i].encode("utf-8")
                line = [(None, "U", text)]
            else:
                line = [(None, "U", b"")]

            yield line


class ANSIWidget(urwid.Widget):
    _sizing = frozenset([urwid.widget.BOX, urwid.widget.FLOW])

    ANSI_ESCAPE_PATTERN = re.compile(r"\x1b\[[0-9;]*m")

    def __init__(self, text: str = "") -> None:
        self.lines = text.split("\n")

        while self.lines:
            clean_last_line = self.ANSI_ESCAPE_PATTERN.sub("", self.lines[-1]).strip()
            if not clean_last_line:
                self.lines.pop()
            else:
                break

        self._display_width = self._calculate_display_width()

    def _calculate_display_width(self) -> int:
        """Calculate the actual display width by stripping ANSI escape sequences."""
        if not self.lines:
            return 0
        max_width = 0
        for line in self.lines:
            clean_line = self.ANSI_ESCAPE_PATTERN.sub("", line)

            width = len(clean_line)
            max_width = max(max_width, width)
        return max_width

    def set_content(self, lines: List[str]) -> None:
        self.lines = lines

        while self.lines:
            clean_last_line = self.ANSI_ESCAPE_PATTERN.sub("", self.lines[-1]).strip()
            if not clean_last_line:
                self.lines.pop()
            else:
                break
        self._display_width = self._calculate_display_width()
        self._invalidate()

    def render(self, size: Tuple[int, ...], focus: bool = False) -> urwid.canvas.Canvas:
        canvas = ANSICanvas(size, self.lines)
        return canvas

    def rows(self, size: Tuple[int, ...], focus: bool = False) -> int:
        return len(self.lines)

    def pack(
        self, size: Optional[Tuple[int, ...]] = None, focus: bool = False
    ) -> Tuple[int, int]:
        """Return the natural size of the widget (width, height)."""
        return (self._display_width, len(self.lines))


if __name__ == "__main__":
    txt = "\x1b[34;47mHello World\x1b[0m"

    urwid.MainLoop(
        urwid.Pile(
            [
                urwid.Filler(urwid.Text(f"TextWidget: {txt}")),
                urwid.Filler(ANSIWidget(f"ANSIWidget: {txt}")),
            ]
        )
    ).run()
