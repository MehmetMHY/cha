from cha import config


def apply_style(text, style_type, style_name):
    TERMINAL_CODES = config.TERMINAL_THEME_CODES
    if style_type not in TERMINAL_CODES or style_name not in TERMINAL_CODES[style_type]:
        return text
    return f"{TERMINAL_CODES[style_type][style_name]}{text}{TERMINAL_CODES['reset']}"


def red(text):
    return apply_style(text, "colors", "red")


def green(text):
    return apply_style(text, "colors", "green")


def yellow(text):
    return apply_style(text, "colors", "yellow")


def blue(text):
    return apply_style(text, "colors", "blue")


def magenta(text):
    return apply_style(text, "colors", "magenta")


def cyan(text):
    return apply_style(text, "colors", "cyan")


def white(text):
    return apply_style(text, "colors", "white")


def black(text):
    return apply_style(text, "colors", "black")


def bold(text):
    return apply_style(text, "styles", "bold")


def underline(text):
    return apply_style(text, "styles", "underline")


def background_black(text):
    return apply_style(text, "backgrounds", "black")


def background_red(text):
    return apply_style(text, "backgrounds", "red")


def background_green(text):
    return apply_style(text, "backgrounds", "green")


def background_yellow(text):
    return apply_style(text, "backgrounds", "yellow")


def background_blue(text):
    return apply_style(text, "backgrounds", "blue")


def background_magenta(text):
    return apply_style(text, "backgrounds", "magenta")


def background_cyan(text):
    return apply_style(text, "backgrounds", "cyan")


def background_white(text):
    return apply_style(text, "backgrounds", "white")


def reset(text):
    return f"{config.TERMINAL_THEME_CODES['reset']}{text}"
