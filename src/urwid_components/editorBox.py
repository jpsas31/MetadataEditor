import urwid


class EditorBox(urwid.Edit):
    def __init__(
        self,
        caption="",
        edit_text="",
        multiline=False,
        align=urwid.Align.LEFT,
        wrap=urwid.WrapMode.SPACE,
        allow_tab=False,
        edit_pos=None,
        layout=None,
        mask=None,
        tag="",
        modifier=None,
    ):
        super().__init__(
            caption,
            edit_text,
            multiline,
            align,
            wrap,
            allow_tab,
            edit_pos,
            layout,
            mask,
        )
        self.tag = tag
        self.modifier = modifier

    def keypress(
        self,
        size: tuple[int],
        key: str,
    ) -> str | None:
        textoInfo = super().get_text()[0]
        modifier = self.modifier()
        if key == "enter":
            if self.tag == "title":
                modifier.change_title(textoInfo)
            elif self.tag == "album":
                modifier.change_album(textoInfo)
            elif self.tag == "artist":
                modifier.change_artist(textoInfo)
            return None

        return super().keypress(size, key)
