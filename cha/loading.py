import itertools
import threading
import sys
import time
import random
from cha import colors

loading_active = False

# ANSI escape codes for cursor control
HIDE_CURSOR = "\033[?25l"
SHOW_CURSOR = "\033[?25h"

# https://stackoverflow.com/questions/2685435/cooler-ascii-spinners
loading_animations = {
    "basic": ["|", "/", "-", "\\"],
    "vertical_bar": [
        "▉",
        "▊",
        "▋",
        "▌",
        "▍",
        "▎",
        "▏",
        "▎",
        "▍",
        "▌",
        "▋",
        "▊",
        "▉",
    ],
    "dots": ["▖", "▘", "▝", "▗"],
    "triangles": ["◢", "◣", "◤", "◥"],
    "rectangles": ["◰", "◳", "◲", "◱"],
    "circles": ["◴", "◷", "◶", "◵"],
    "halfcircles": ["◐", "◓", "◑", "◒"],
    "braille": [
        "⣾",
        "⣽",
        "⣻",
        "⢿",
        "⡿",
        "⣟",
        "⣯",
        "⣷",
        "⠁",
        "⠂",
        "⠄",
        "⡀",
        "⢀",
        "⠠",
        "⠐",
        "⠈",
    ],
}


def loading_animation(text="Thinking"):
    frames = random.choice(list(loading_animations.values()))
    spinner = itertools.cycle(frames)

    # hide cursor at start
    sys.stdout.write(HIDE_CURSOR)
    sys.stdout.flush()

    try:
        while loading_active:
            sys.stdout.write(colors.green(f"\r{text} {next(spinner)}"))
            sys.stdout.flush()
            time.sleep(0.1)
        # clear line without moving to the next line
        sys.stdout.write("\r" + " " * (len(text) + 10) + "\r")
        sys.stdout.flush()
    finally:
        # always show cursor before exiting, even if there's an error
        sys.stdout.write(SHOW_CURSOR)
        sys.stdout.flush()


def start_loading(text="Thinking"):
    global loading_active
    loading_active = True
    loading_thread = threading.Thread(target=loading_animation, args=(text,))
    loading_thread.daemon = True
    loading_thread.start()
    return loading_thread


def stop_loading(loading_thread):
    global loading_active
    if loading_active:
        loading_active = False
        if loading_thread:
            loading_thread.join()
