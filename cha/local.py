from importlib.metadata import version
from pathlib import Path
import inspect
import json
import sys
import os

from cha import config, colors


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


def validate_tools(tools):
    # NOTE: this is hard coded but valid
    TOOL_MOST_HAVE_VARIABLES = {
        "name": {"type": str, "required": True},
        "description": {"type": str, "required": True},
        "alias": {"type": str, "required": True},
        "include_history": {"type": [bool, int], "required": False, "default": False},
        "timeout_sec": {"type": int, "required": False, "default": 15},
        "pipe_input": {"type": bool, "required": False, "default": False},
        "pipe_output": {"type": bool, "required": False, "default": True},
    }

    valid = []
    invalid = []
    errors = []

    for tool in tools:
        # a friendly identifier string for error messages
        tool_id = getattr(tool, "name", repr(tool))

        # collect this tool's errors
        tool_errors = []

        for var_name, spec in TOOL_MOST_HAVE_VARIABLES.items():
            required = spec.get("required", False)
            has_default = "default" in spec
            default = spec.get("default")
            expected_type = spec["type"]

            # normalize to a tuple of types
            if isinstance(expected_type, list):
                expected_types = tuple(expected_type)
            else:
                expected_types = (expected_type,)

            # check for missing attributes
            if not hasattr(tool, var_name):
                if required:
                    tool_errors.append(f"missing required attribute '{var_name}'")
                else:
                    # fill in default for optional
                    setattr(tool, var_name, default)
                continue

            # check if required attributes are none or not
            val = getattr(tool, var_name)
            if val is None:
                if required:
                    tool_errors.append(f"attribute '{var_name}' is None but required")
                else:
                    setattr(tool, var_name, default)
                continue

            # validate that each attribute is the current type
            if not isinstance(val, expected_types):
                tool_errors.append(
                    f"attribute '{var_name}' expected type "
                    f"{expected_types}, got {type(val)}"
                )

        # decide valid/invalid
        if tool_errors:
            invalid.append(tool)
            # prefix each message with tool_id
            for msg in tool_errors:
                errors.append(f"{tool_id}: {msg}")
        else:
            valid.append(tool)

    return valid, invalid, errors


def get_tools():
    if len(config.EXTERNAL_TOOLS) == 0:
        return []

    valid_tools, invalid_tools, tool_errors = validate_tools(config.EXTERNAL_TOOLS)

    if len(invalid_tools) > 0:
        print(colors.red("Errors well loading tools:"))
        for err in tool_errors:
            print(colors.red(f"- {err}"))

    if len(valid_tools) == 0:
        return []

    return valid_tools


if __name__ == "__main__":
    tools = get_tools()

    print(tools)

    sys.exit(0)

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
