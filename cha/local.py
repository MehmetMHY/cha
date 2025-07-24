from datetime import datetime, timezone
import subprocess
import importlib
import signal
import json
import os

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


def browse_and_select_history_file(exact_mode=False):
    from cha import utils
    import glob

    history_dir = os.path.join(os.environ["HOME"], ".cha", "history")
    if not os.path.isdir(history_dir):
        return None

    selected_path = None
    try:
        json_files = glob.glob(os.path.join(history_dir, "*.json"))
        if not json_files:
            return None

        rg_command = [
            "rg",
            "--line-number",
            "--color=always",
            "",
            "--glob",
            "*.json",
            history_dir,
        ]

        header_text = "{} | [Shift↑/↓] [ESC] [ENTER]".format(
            "EXACT (use 'query' for literal)" if exact_mode else "FUZZY"
        )
        fzf_command = [
            "fzf",
            "--ansi",
            "--delimiter",
            ":",
            "--preview",
            "jq -r '.chat[] | \"User: \\(.user)\\n\\(.bot)\\n\"' {1} | bat --color=always --style=numbers --pager=never",
            "--preview-window=right,60%,wrap",
            "--header",
            header_text,
        ]
        if exact_mode:
            fzf_command.append("--exact")

        rg_process = subprocess.run(
            rg_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        if rg_process.returncode != 0 and rg_process.returncode != 1:
            return None

        fzf_result = utils.run_fzf_ssh_safe(fzf_command, rg_process.stdout)
        if not fzf_result:
            return None

        selected_line = fzf_result.strip()
        if selected_line:
            selected_path = selected_line.split(":", 1)[0]

    except (subprocess.CalledProcessError, KeyboardInterrupt):
        return None
    except Exception:
        return None

    if not selected_path or not os.path.exists(selected_path):
        return None

    try:
        file_content = read_json(selected_path)
        chat_content = file_content
        if file_content.get("chat") != None:
            chat_content = file_content.get("chat")
        return {"path": selected_path, "content": file_content, "chat": chat_content}
    except Exception:
        return None


def print_history_browse_and_select_history_file(chat, include_timestamp=True):
    for msg in chat[1:]:
        timestamp = msg.get("time")
        user = msg.get("user")
        bot = msg.get("bot")

        timestamp_str = ""
        if include_timestamp and timestamp:
            try:
                dt_object = datetime.fromtimestamp(timestamp, tz=timezone.utc)
                timestamp_str = f"[{dt_object.strftime('%Y-%m-%d %H:%M:%S %Z')}] "
            except (TypeError, ValueError):
                timestamp_str = f"[{timestamp}] "

        if user:
            print(
                colors.red(timestamp_str) + colors.blue("User: ") + colors.white(user)
            )

        if bot:
            print(colors.green(bot))

    return
