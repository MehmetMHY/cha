from importlib.metadata import version
from pathlib import Path
import json
import os

from cha import utils


def load_json(file_path):
    with open(file_path, "r") as file:
        data = json.load(file)
    return data


def setup_cha_config_dir():
    home_dir = os.path.expanduser("~")
    cha_dir = os.path.join(home_dir, ".cha")
    settings_file = os.path.join(cha_dir, "config.py")
    history_dir = os.path.join(cha_dir, "history")
    tools_dir = os.path.join(cha_dir, "tools")

    # create .cha directory if it doesn't exist
    if not os.path.exists(cha_dir):
        os.makedirs(cha_dir)
    else:
        return

    # create settings.json with default content if it doesn't exist
    default_settings = {
        "version": None,
        "history": False,
        "settings": {},
        "url": "https://github.com/MehmetMHY/cha",
    }
    try:
        default_settings["version"] = version("cha")
    except:
        pass

    if not os.path.isfile(settings_file):
        with open(settings_file, "w") as f:
            json.dump(default_settings, f, indent=4)

    # create history directory if it doesn't exist
    if not os.path.exists(history_dir):
        os.makedirs(history_dir)

    # create tools directory if it doesn't exist
    if not os.path.exists(tools_dir):
        os.makedirs(tools_dir)

    return


if __name__ == "__main__":
    setup_cha_config_dir()

    cha_config_dir = os.path.join(str(Path.home()), ".cha/")

    cha_config_file = os.path.join(cha_config_dir, "config.json")

    cha_saved_history_dir = os.path.join(cha_config_dir, "history/")

    cha_tools_dir = os.path.join(cha_config_dir, "tools/")

    print(cha_config_dir)
    print()
    print(cha_config_file)
    print()
    print(cha_saved_history_dir)
    print()
    print(cha_tools_dir)

    cha_config = utils.read_json(cha_config_file)

    print(json.dumps(cha_config, indent=4))
