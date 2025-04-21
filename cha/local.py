from importlib.metadata import version
from pathlib import Path
import signal
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
    valid = []
    invalid = []
    errors = []
    seen_names = set()

    for tool in tools:
        tool_id = getattr(tool, "name", repr(tool))
        tool_errors = []

        for var_name, spec in config.TOOL_MOST_HAVE_VARIABLES.items():
            required = spec.get("required", False)
            has_default = "default" in spec
            default = spec.get("default")
            expected_type = spec["type"]

            if isinstance(expected_type, list):
                expected_types = tuple(expected_type)
            else:
                expected_types = (expected_type,)

            if not hasattr(tool, var_name):
                if required:
                    tool_errors.append(f"missing required attribute '{var_name}'")
                else:
                    setattr(tool, var_name, default)
                continue

            val = getattr(tool, var_name)
            if val is None:
                if required:
                    tool_errors.append(f"attribute '{var_name}' is None but required")
                else:
                    setattr(tool, var_name, default)
                continue

            if not isinstance(val, expected_types):
                tool_errors.append(
                    f"attribute '{var_name}' expected type "
                    f"{expected_types}, got {type(val)}"
                )

        # Check for duplicate 'name' value
        name = getattr(tool, "name", None)
        if name is not None:
            if name in seen_names:
                tool_errors.append(f"duplicate tool name '{name}' is not allowed")
            seen_names.add(name)

        if tool_errors:
            invalid.append(tool)
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

    advance_tools = []
    for tool in valid_tools:
        tmp = tool.__dict__
        for key in config.TOOL_MOST_HAVE_VARIABLES:
            if key not in tmp:
                tmp[key] = config.TOOL_MOST_HAVE_VARIABLES[key]["default"]
        tmp["pointer"] = tool
        advance_tools.append(tmp)

    return advance_tools


def execute_tool(tool_data, chat_history=None, piped_question=None):
    class TimeoutException(Exception):
        pass

    def timeout_handler(signum, frame):
        raise TimeoutException("Operation timed out!")

    output = {}

    args = {}
    if tool_data["include_history"] == True and chat_history != None:
        args["chat_history"] = chat_history
    if tool_data["pipe_input"] == True and piped_question != None:
        args["piped_input"] = piped_question

    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(tool_data["timeout_sec"])
    try:
        output["result"] = tool_data["pointer"].execute(**args)
        output["error"] = None
    except TimeoutException as e:
        output["error"] = "Timed out the tool"
        output["result"] = None
    except Exception as e:
        output["error"] = f"{e}"
        output["result"] = None
    finally:
        signal.alarm(0)

    output["continue"] = tool_data["pipe_output"]

    return output
