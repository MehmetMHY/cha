import re


def normalize_whitespace(text: str, tab_size: int = 4) -> str:
    """
    Replaces various (often-unnoticed) whitespace characters with standard spaces,
    collapses consecutive spaces in the 'middle' of the text, and preserves all
    leading and trailing spaces exactly as they appear (after converting any
    special characters to spaces but not collapsing them).
    """

    # mapping of special whitespace characters to their replacements
    whitespace_map = {
        "\t": " " * tab_size,  # replace tabs with a specified number of spaces
        "\n": " ",  # replace newlines with single spaces
        "\r": " ",  # replace carriage returns with single spaces
        "\u00a0": " ",  # non-breaking space
        "\u2000": " ",  # en/em and other Unicode spaces
        "\u2001": " ",
        "\u2002": " ",
        "\u2003": " ",
        "\u2004": " ",
        "\u2005": " ",
        "\u2006": " ",
        "\u2007": " ",
        "\u2008": " ",
        "\u2009": " ",
        "\u200a": " ",
    }

    # extract leading and trailing whitespace
    leading_match = re.match(r"^\s+", text)
    leading = leading_match.group() if leading_match else ""
    trailing_match = re.search(r"\s+$", text)
    trailing = trailing_match.group() if trailing_match else ""

    # NOTE: the middle portion is whatever is left after removing detected leading/trailing
    middle = text[len(leading) : len(text) - len(trailing)]

    # replace special whitespace in each portion
    for char, replacement in whitespace_map.items():
        leading = leading.replace(char, replacement)
        trailing = trailing.replace(char, replacement)
        middle = middle.replace(char, replacement)

    # collapse consecutive spaces only in the middle portion
    middle = re.sub(r"\s+", " ", middle)

    # reconstruct the string with original leading and trailing space counts
    return leading + middle + trailing


def count_leading_ws(s: str) -> int:
    match = re.match(r"^\s*", s)
    if match:
        return len(match.group())
    return 0


def rls(text: str, fast_mode: bool = False) -> str:
    lines = text.split("\n")

    lc = 0
    for line in lines:
        if fast_mode == False:
            line = normalize_whitespace(line)
        c = count_leading_ws(line)
        if (lc > c and c > 0) or (lc == 0 and c > lc):
            lc = c

    if lc == 0:
        return text

    output = ""
    for line in lines:
        if len(line) >= lc:
            output = output + line[lc:] + "\n"
        else:
            output += "\n"

    return output.strip()
