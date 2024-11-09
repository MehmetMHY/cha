import itertools
import threading
import sys
import time
from cha import colors

loading_active = False


def loading_animation(text="Thinking"):
    spinner = itertools.cycle(["-", "\\", "|", "/"])
    while loading_active:
        sys.stdout.write(colors.green(f"\r{text} {next(spinner)}"))
        sys.stdout.flush()
        time.sleep(0.1)
    # clear line without moving to the next line
    sys.stdout.write("\r" + " " * (len(text) + 10) + "\r")
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
