# general
def reset(text): return f"\033[0m{text}"

# colors
def red(text): return f"\033[91m{text}\033[0m"
def green(text): return f"\033[92m{text}\033[0m"
def yellow(text): return f"\033[93m{text}\033[0m"
def blue(text): return f"\033[94m{text}\033[0m"
def magenta(text): return f"\033[95m{text}\033[0m"
def cyan(text): return f"\033[96m{text}\033[0m"
def white(text): return f"\033[97m{text}\033[0m"
def black(text): return f"\033[30m{text}\033[0m"

# styles
def bold(text): return f"\033[1m{text}\033[0m"
def underline(text): return f"\033[4m{text}\033[0m"
def background_black(text): return f"\033[40m{text}\033[0m"
def background_red(text): return f"\033[41m{text}\033[0m"
def background_green(text): return f"\033[42m{text}\033[0m"
def background_yellow(text): return f"\033[43m{text}\033[0m"
def background_blue(text): return f"\033[44m{text}\033[0m"
def background_magenta(text): return f"\033[45m{text}\033[0m"
def background_cyan(text): return f"\033[46m{text}\033[0m"
def background_white(text): return f"\033[47m{text}\033[0m"

