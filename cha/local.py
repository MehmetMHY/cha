from importlib.metadata import version
from pathlib import Path
import json
import os


def setup_cha_config_dir():
    try:
        home_dir = os.path.expanduser("~")
        cha_dir = os.path.join(home_dir, ".cha")
        settings_file = os.path.join(cha_dir, "config.py")
        history_dir = os.path.join(cha_dir, "history")
        tools_dir = os.path.join(cha_dir, "tools")

        # create .cha directory if it doesn't exist
        if not os.path.exists(cha_dir):
            os.makedirs(cha_dir)
        else:
            return False

        # create config file
        if not os.path.isfile(settings_file):
            with open(settings_file, "w") as file:
                file.write("")

        # create history directory if it doesn't exist
        if not os.path.exists(history_dir):
            os.makedirs(history_dir)

        # create tools directory if it doesn't exist
        if not os.path.exists(tools_dir):
            os.makedirs(tools_dir)

        return True
    except:
        return None


if __name__ == "__main__":
    output = setup_cha_config_dir()

    cha_config_dir = os.path.join(str(Path.home()), ".cha/")

    if output == None:
        print(
            f"An unexpected error happened well trying to create the Cha config directory"
        )
    else:
        print("CHA INIT RAW OUTPUT:  ", output, f"(False = Config Dir Exists)")
        print("CHA CONFIG DIRECTORY: ", os.path.join(str(Path.home()), ".cha/"))
        print("CHA CONFIG FILEPATH:  ", os.path.join(cha_config_dir, "config.py"))
        print("CHA HISTORY DIRECTORY:", os.path.join(cha_config_dir, "history/"))
        print("CHA TOOLS DIRECTORY:  ", os.path.join(cha_config_dir, "tools/"))
