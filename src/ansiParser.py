import re

# ansi has the sequence style->foreground color->background color
# special case when use 256 color mode
# style-> 38 -> 5 -> {ID}m	Set foreground color where {ID} is a number between 0 and 255.
# style-> 48 -> 5 -> {ID}m	Set background color where {ID} is a number between 0 and 255.

ANSI_ESCAPE_PATTERN = re.compile(r"\x1b\[[0-9;]*[a-zA-Z]")


ANSI_ESCAPE_CODES_REVERSE = 20
SEPARATOR = ", "
ANSI_ESCAPE_CODES = {
    "1": "bold",  # to return to normal use 22
    "3": "italics",  # to return to normal add ANSI_ESCAPE_CODES_REVERSE
    "4": "underline",
    "5": "blink",  # to return to normal add ANSI_ESCAPE_CODES_REVERSE
    "7": "standout",  # to return to normal add ANSI_ESCAPE_CODES_REVERSE
    "9": "strikethrough",  # to return to normal add ANSI_ESCAPE_CODES_REVERSE
}


def rgb_to_hex(rgb_tuple):
    # Use format specification mini-language:
    # :02X means:
    # 0: Pad with zeros
    # 2: Ensure a width of 2
    # X: Convert to uppercase hexadecimal format

    return "#{:02X}{:02X}{:02X}".format(*rgb_tuple)


def get_squeezed_indices(text: str) -> list[tuple[int, int]]:
    indices = []

    indices.extend(
        [(match.start(), match.end()) for match in re.finditer(ANSI_ESCAPE_PATTERN, text)]
    )

    squeezed_indices = [indices[0]]

    for index in indices:
        if squeezed_indices[-1][1] == index[0]:
            squeezed_indices[-1][1] = index[1]
        else:
            squeezed_indices.append(index)

    return squeezed_indices


def ansi_text_parser(text: str, attr_list: list[tuple[str, str]]) -> list[tuple[str, str]]:
    squeezed_indices = get_squeezed_indices(text)
    texts = []

    for i, index in enumerate(squeezed_indices):
        span = (
            index[1],
            squeezed_indices[i + 1][0] if i < len(squeezed_indices) - 1 else len(text),
        )

        value = text[span[0] : span[1]]
        if len(value) > 0:
            texts.append(value)

    return list(zip(attr_list, texts))


def ansi_attr_parser(text: str) -> list[tuple[str, str]]:
    matches = []
    attr_list = []
    matches.extend([match for match in re.finditer(ANSI_ESCAPE_PATTERN, text)])

    is_foreground = False
    is_background = False
    is_rgb = False
    rgb_values = []
    is_256 = False
    attr_spec_fg = ""
    attr_spec_bg = ""

    for index, match in enumerate(matches):
        vals = match.group().replace("\x1b[", "").replace("m", "").split(";")
        end_index = match.end()

        for val in vals:
            if not is_256 and not is_rgb:
                if val == "0":
                    continue

                if not is_background and not is_foreground:
                    if val in ANSI_ESCAPE_CODES:
                        attr_spec_fg += f"{ANSI_ESCAPE_CODES[val]}{SEPARATOR}"
                        continue

                    if int(val) in range(30, 38) or int(val) in range(
                        90, 97
                    ):  # Standard Foreground colors.
                        attr_spec_fg += "h" + val + SEPARATOR
                        continue

                    if int(val) in range(40, 48) or int(val) in range(
                        100, 107
                    ):  # Standard Background colors.
                        attr_spec_bg += "h" + val + SEPARATOR
                        continue

                if val == "38":
                    is_foreground = True
                    continue

                if val == "48":
                    is_background = True
                    continue

                if val == "2":
                    is_rgb = True
                    continue

                if val == "5":
                    is_256 = True
                    continue

            if is_rgb:
                rgb_values.append(int(val))
                if len(rgb_values) == 3:
                    is_rgb = False
                    if is_foreground:
                        is_foreground = False
                        attr_spec_fg += rgb_to_hex(rgb_values) + SEPARATOR

                    if is_background:
                        is_background = False
                        attr_spec_bg += rgb_to_hex(rgb_values) + SEPARATOR

                    rgb_values = []

                continue

            if is_256:
                if is_foreground:
                    is_foreground = False
                    is_256 = False
                    attr_spec_fg += "h" + val + SEPARATOR
                if is_background:
                    is_background = False
                    is_256 = False
                    attr_spec_bg += "h" + val + SEPARATOR

        if index < len(matches) - 1 and end_index == matches[index + 1].start():
            continue

        if len(attr_spec_fg) > 0 and attr_spec_fg[-2] == ",":
            attr_spec_fg = attr_spec_fg[:-2]
        if len(attr_spec_bg) > 0 and attr_spec_bg[-2] == ",":
            attr_spec_bg = attr_spec_bg[:-2]

        if attr_spec_fg == "":
            attr_spec_fg = None
        if attr_spec_bg == "":
            attr_spec_bg = None

        attr_list.append((attr_spec_fg, attr_spec_bg))
        attr_spec_fg = ""
        attr_spec_bg = ""

    return attr_list


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

    for t in texts:
        attr_list = ansi_attr_parser(t)
        print(attr_list)
        ansi_text = ansi_text_parser(t, attr_list)
        print(ansi_text)


if __name__ == "__main__":
    main()
