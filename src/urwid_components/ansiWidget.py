from typing import Any, Iterable, List, Optional, Tuple

import urwid


class ANSICanvas(urwid.canvas.Canvas):
    def __init__(self, size: Tuple[int, ...], text_lines: List[str]) -> None:
        super().__init__()

        # Handle both single-dimensional (width) and two-dimensional (width, height) sizing
        if len(size) == 1:
            self.maxcols = size[0]
            self.maxrows = len(text_lines)  # Height is determined by the number of lines
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
            else:
                text = b""

            padding = bytes().rjust(max(0, cols - len(text)))
            line = [(None, "U", text + padding)]

            yield line


class ANSIWidget(urwid.Widget):
    _sizing = frozenset([urwid.widget.BOX, urwid.widget.FLOW])  # Support both BOX and FLOW sizing

    def __init__(self, text: str = "") -> None:
        self.lines = text.split("\n")

    def set_content(self, lines: List[str]) -> None:
        self.lines = lines
        self._invalidate()

    def render(self, size: Tuple[int, ...], focus: bool = False) -> urwid.canvas.Canvas:
        canvas = ANSICanvas(size, self.lines)
        return canvas

    def rows(self, size: Tuple[int, ...], focus: bool = False) -> int:
        # Return the number of lines in the text
        return len(self.lines)


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