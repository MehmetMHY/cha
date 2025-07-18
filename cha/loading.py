import itertools
import threading
import random
import time
import sys

from cha import colors, config


class LoadingAnimation:
    def __init__(self):
        self.active = False
        self.last_message = ""
        self.message_lock = threading.Lock()
        self.cursor_position = 0

    def _clear_current_line(self):
        # move cursor to start of line and clear it completely
        sys.stdout.write("\r" + " " * 100 + "\r")
        sys.stdout.flush()

    def _update_display(self, text, spinner_char):
        with self.message_lock:
            # move cursor to start of line and clear it
            message = f"{text} {spinner_char}"
            sys.stdout.write(f"\r{colors.green(message)}")
            sys.stdout.flush()
            self.last_message = message

    def loading_animation(self, text="Thinking", animation_type=None):
        if animation_type and animation_type in config.LOADING_ANIMATIONS:
            frames = config.LOADING_ANIMATIONS[animation_type]
        else:
            frames = random.choice(list(config.LOADING_ANIMATIONS.values()))

        spinner = itertools.cycle(frames)

        # hide cursor at start
        sys.stdout.write(config.HIDE_CURSOR)
        sys.stdout.flush()

        try:
            while self.active:
                self._update_display(text, next(spinner))
                time.sleep(0.1)
            # completely clear the line and reset cursor
            sys.stdout.write("\r\033[K")
            sys.stdout.flush()
        finally:
            # always show cursor before exiting
            sys.stdout.write(config.SHOW_CURSOR)
            sys.stdout.flush()

    def print_message(self, message):
        with self.message_lock:
            self._clear_current_line()
            sys.stdout.write(colors.white(str(message)) + "\n")
            sys.stdout.flush()

    def start(self, text="Thinking", animation_type=None):
        """
        text (str): The text to display next to the animation
        animation_type (str): The type of animation to use
        """
        self.active = True
        self.loading_thread = threading.Thread(
            target=self.loading_animation, args=(text, animation_type)
        )
        self.loading_thread.daemon = True
        self.loading_thread.start()
        return self.loading_thread

    def stop(self):
        if self.active:
            self.active = False
            if hasattr(self, "loading_thread"):
                self.loading_thread.join()


# global instance(s)
loader = LoadingAnimation()


def start_loading(text="Thinking", animation_type=None):
    return loader.start(text, animation_type)


def stop_loading():
    loader.stop()


def print_message(message):
    loader.print_message(message)
