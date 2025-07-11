from datetime import datetime, timezone
import subprocess
import importlib
import signal
import json
import os
import re

from cha import config, colors


def _lazy_load_tool(tool_def):
    try:
        module = importlib.import_module(tool_def["module_path"])
        tool_class = getattr(module, tool_def["class_name"])
        return tool_class()
    except Exception as e:
        return None


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
        if isinstance(tool, dict) and tool.get("_lazy_tool"):
            lazy_tool_instance = _lazy_load_tool(tool)
            if lazy_tool_instance is None:
                invalid.append(tool)
                errors.append(
                    f"Failed to load lazy tool: {tool.get('class_name', 'Unknown')}"
                )
                continue
            tool = lazy_tool_instance

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
    if tool_data["pipe_input"] == True:
        args["piped_input"] = piped_question if piped_question else ""

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


def read_json(path):
    with open(str(path)) as file:
        content = json.load(file)
    return content


def browse_and_select_history_file():
    history_dir = os.path.join(os.environ["HOME"], ".cha", "history")

    file_paths = []
    if os.path.isdir(history_dir):
        for filename in os.listdir(history_dir):
            full_path = os.path.join(history_dir, filename)
            if os.path.isfile(full_path) and full_path.endswith(".json"):
                file_paths.append(full_path)

    # multithreading to process files in parallel is needed
    output = {}
    for file_path in file_paths:
        content = read_json(file_path)
        messages = content.get("chat", None)
        if messages is None:
            messages = content

        clean_content = ""
        for msg in messages[1:]:
            if msg.get("user", None) is not None:
                clean_content = clean_content + msg.get("user") + " "
            if msg.get("user", None) is None and msg.get("bot", None) is not None:
                clean_content = clean_content + msg.get("bot") + " "

        # clean up content to better work with selector
        clean_content = re.sub(
            r"https?://\S+|www\.\S+", "", clean_content
        )  # remove urls from the string
        clean_content = re.sub(
            r"([A-Za-z]:\\(?:[^\\\s]+\\)*[^\\\s]+|\/(?:[^\/\s]+\/)*[^\/\s]+)",
            "",
            clean_content,
        )  # remove file/dir paths from string
        clean_content = re.sub(r"\n", "", clean_content)  # remove new lines
        clean_content = re.sub(r"\s+", " ", clean_content)  # remove extra whitespaces

        output[file_path] = clean_content.strip()

    # all the code below apply the fzf integration
    try:
        terminal_width = os.get_terminal_size().columns
    except OSError:
        terminal_width = 80

    # prepare data for fzf, truncating content to fit
    entries = []
    line_to_path_map = {}
    for path, content in output.items():
        basename = os.path.basename(path)
        timestamp_str = "<Unknown Time>"
        epoch_val = float("inf")
        try:
            parts = basename.split("_")
            if len(parts) > 1 and parts[-1].endswith(".json"):
                epoch_part = parts[-1][:-5]
                if epoch_part.isdigit():
                    epoch_val = int(epoch_part)
                    timestamp_str = datetime.fromtimestamp(
                        epoch_val, tz=timezone.utc
                    ).strftime("%Y-%m-%d %H:%M:%S UTC")
        except Exception:
            pass

        prefix = f"[{timestamp_str}] "

        # new display format - using full content
        display_line = f"{prefix}{content}"

        # store entry with epoch value for sorting
        entries.append((epoch_val, display_line, path))

    # if no history files are found, return None
    if len(entries) == 0:
        return None

    # attempt to sort entries by epoch (newest to oldest)
    entries.sort(key=lambda x: x[0], reverse=True)
    fzf_input_lines = [entry[1] for entry in entries]
    line_to_path_map = {entry[1]: entry[2] for entry in entries}
    fzf_input_string = "\n".join(fzf_input_lines)

    selected_path = None
    try:
        try:
            fzf_process = subprocess.run(
                [
                    "fzf",
                    "--exact",
                    "-e",
                    "--delimiter",
                    "\\t",
                    "--with-nth",
                    "1",
                    "-i",  # case-insensitive flag
                ],
                input=fzf_input_string,
                capture_output=True,
                text=True,
                check=True,  # raise exception on non-zero exit code (e.g., user pressing Esc)
                encoding="utf-8",
            )
            selected_line = fzf_process.stdout.strip()
            selected_path = line_to_path_map[selected_line]
        except KeyboardInterrupt:
            pass
    except Exception as e:
        pass

    file_content = read_json(selected_path)
    chat_content = file_content
    if file_content.get("chat") != None:
        chat_content = file_content.get("chat")

    return {"path": selected_path, "content": file_content, "chat": chat_content}


def print_history_browse_and_select_history_file(chat, include_timestamp=True):
    # NOTE: make sure to send the entire chat history, ALL of it!
    for msg in chat[1:]:
        timestamp = msg.get("time")
        user = msg.get("user")
        bot = msg.get("bot")

        timestamp_str = ""
        if include_timestamp and timestamp:
            timestamp_str = f"[{int(timestamp)}] "

        if user:
            print(
                colors.red(timestamp_str) + colors.blue("User: ") + colors.white(user)
            )

        if bot:
            print(colors.green(bot))

    return
