import subprocess
import traceback
import argparse
import time
import uuid
import json
import sys
import os
import re

try:
    from cha import colors, utils, config, loading, platforms
    from cha.client import (
        get_current_chat_client,
        set_current_chat_client,
    )
except (KeyboardInterrupt, EOFError):
    sys.exit(1)


CURRENT_CHAT_HISTORY = [
    {
        "time": time.time(),
        "user": config.INITIAL_PROMPT,
        "bot": "",
        "platform": config.CHA_CURRENT_PLATFORM_NAME,
        "model": config.CHA_DEFAULT_MODEL,
    }
]

# track visited directories for exit display
VISITED_DIRECTORIES = []


def format_visited_directories(directories):
    """
    format visited directories for exit display
    """
    if not directories:
        return ""

    if len(directories) == 1:
        return directories[0]
    elif len(directories) == 2:
        return f"{directories[0]} & {directories[1]}"
    else:
        # more than 2 directories
        formatted = ", ".join(directories[:-1])
        formatted += f" & {directories[-1]}"
        return formatted


def backtrack_history(chat_history):
    """
    Allow users to select multiple chat messages to remove from history using fzf.
    Returns a list of selected indices to remove, or None if cancelled.
    """
    try:
        history_items = []
        for i, msg in enumerate(chat_history[1:], 1):
            user_msg = msg.get("user", "").replace("\n", " ").strip()
            user_msg = re.sub(r"\s+", " ", user_msg)
            timestamp = time.strftime("%H:%M:%S", time.localtime(msg["time"]))
            history_items.append(f"[{i}] ({timestamp}) {user_msg}")

        history_items = history_items[::-1]

        try:
            from cha import utils

            selected_output = utils.run_fzf_ssh_safe(
                [
                    "fzf",
                    "--reverse",
                    "--height=40%",
                    "--border",
                    "--multi",
                    "--prompt=TAB to multi-select chats to remove, ENTER to confirm: ",
                ],
                "\n".join(history_items),
            )
            if not selected_output:
                return None

            selected_indices = []
            for line in selected_output.split("\n"):
                if line.strip():
                    index_match = re.match(r"\[(\d+)\]", line)
                    if index_match:
                        selected_indices.append(int(index_match.group(1)))

            return selected_indices if selected_indices else None

        except (subprocess.CalledProcessError, subprocess.SubprocessError):
            return None

    except Exception as e:
        print(colors.red(f"Error during backtrack: {e}"))
        return None


def get_help_options():
    help_options = []
    bracket_options = []

    help_options.append(f"{config.HELP_ALL_ALIAS} - Show all help options")
    help_options.append(f"{config.EXIT_STRING_KEY} - Exit chat or CTRL-C")
    help_options.append(f"{config.CLEAR_HISTORY_TEXT} - Clear chat history")
    help_options.append(f"{config.LOAD_MESSAGE_CONTENT} - Load files (simple mode)")
    help_options.append(
        f"{config.LOAD_MESSAGE_CONTENT_ADVANCED} - Load files (advanced mode)"
    )
    help_options.append(
        f"{config.RUN_ANSWER_FEATURE} - Web search or '{config.RUN_ANSWER_FEATURE} <query>' for quick search"
    )
    help_options.append(f"{config.RECORD_AUDIO_ALIAS} - Record voice prompt")
    help_options.append(f"{config.TEXT_EDITOR_INPUT_MODE} - Text-editor input mode")
    help_options.append(
        f"{config.SWITCH_MODEL_TEXT} - Switch between models during a session"
    )
    help_options.append(
        f"{config.SWITCH_PLATFORM_TEXT} - Switch between platforms during a session"
    )
    help_options.append(f"{config.USE_CODE_DUMP} - Codedump a directory as context")
    help_options.append(
        f"{config.PICK_AND_RUN_A_SHELL_OPTION} - Open shell or run command (e.g. !x ls)"
    )
    help_options.append(
        f"{config.ENABLE_OR_DISABLE_AUTO_SD} - Enable or disable auto url detection and scraping"
    )
    help_options.append(
        f"{config.RUN_EDITOR_ALIAS} - Interactive file editor with diff and shell access"
    )
    help_options.append(
        f"{config.BACKTRACK_HISTORY_KEY} - Select and remove specific chats from history"
    )
    help_options.append(
        f"{config.CHANGE_DIRECTORY_ALIAS} - Navigate and change cha's current directory"
    )
    help_options.append(f"{config.SKIP_SEND_TEXT} - Skip sending current input")
    help_options.append(f"{config.HELP_PRINT_OPTIONS_KEY} - List all options")

    bracket_options.append(
        f"{config.MULTI_LINE_MODE_TEXT} - Multi-line switching (type '{config.MULTI_LINE_SEND}' to send)"
    )
    bracket_options.append(f"{config.SAVE_CHAT_HISTORY} - Save chat history")
    bracket_options.append(
        f"{config.EXPORT_FILES_IN_OUTPUT_KEY} [all/single] - Export files from response(s)"
    )
    bracket_options.append(
        f"{config.SAVE_CHAT_HISTORY} [text/txt] - Save chat history as JSON (default) or text file"
    )

    if os.path.isdir(config.LOCAL_CHA_CONFIG_HISTORY_DIR):
        help_options.append(
            f"{config.LOAD_HISTORY_TRIGGER} [exact] - Search history (fuzzy by default)"
        )

    help_options.extend(bracket_options)

    external_tools = config.get_external_tools_execute()
    if len(external_tools) > 0:
        for tool in external_tools:
            alias = tool["alias"]
            about = re.sub(r"[.!?]+$", "", tool["description"].lower())
            help_options.append(f"{alias} - {about}")

    return help_options


def interactive_help(selected_model):
    help_options = get_help_options()

    try:
        from cha import utils

        selected_output = utils.run_fzf_ssh_safe(
            [
                "fzf",
                "--reverse",
                "--height=40%",
                "--border",
                "--prompt=TAB to multi-select, ENTER to confirm, & Esc to cancel: ",
                "--multi",
                "--exact",
                "--header",
                f"Chatting On {config.CHA_CURRENT_PLATFORM_NAME.upper()} With {selected_model}",
            ],
            "\n".join(help_options),
        )
        if selected_output:
            selected_items = selected_output.split("\n")

            # handle single selection - check if it's a parameter-less alias
            if len(selected_items) == 1:
                item = selected_items[0]

                # show all help if [ALL] is selected
                if config.HELP_ALL_ALIAS in item:
                    print(
                        colors.yellow(
                            f"Chatting On {config.CHA_CURRENT_PLATFORM_NAME.upper()} With {selected_model}"
                        )
                    )
                    for help_item in help_options:
                        if config.HELP_ALL_ALIAS not in help_item:
                            print(colors.yellow(help_item))
                    return None

                # check if this is a parameter-less alias that can be executed
                alias = item.split(" - ")[0] if " - " in item else ""

                # get parameter-less aliases from config
                parameter_less_aliases = config.PARAMETER_LESS_ALIASES.copy()

                # add external tool aliases that don't require parameters
                external_tools = config.get_external_tools_execute()
                for tool in external_tools:
                    if not tool.get(
                        "pipe_input", False
                    ):  # tools that don't require input parameters
                        parameter_less_aliases.append(tool["alias"])

                # check if this alias can be executed directly
                if alias in parameter_less_aliases:
                    return alias

                # if it's not a parameter-less alias, just print it
                print(colors.yellow(item))
                return None

            # handle multiple selections - just print them
            else:
                for item in selected_items:
                    if config.HELP_ALL_ALIAS not in item:
                        print(colors.yellow(item))
                return None

    except (subprocess.CalledProcessError, subprocess.SubprocessError):
        pass

    return None


def title_print(selected_model):
    print(
        colors.yellow(
            f"Chatting With {config.CHA_CURRENT_PLATFORM_NAME.upper()} Model: {selected_model}"
        )
    )
    help_options = get_help_options()
    for option in help_options:
        if config.HELP_ALL_ALIAS not in option:
            print(colors.yellow(f"- {option}"))


def list_models():
    from cha import utils

    if config.CHA_CURRENT_PLATFORM_NAME == "openai":
        response = get_current_chat_client().models.list()
        if not response.data:
            raise ValueError("No models available")

        models = []
        for model in response.data:
            if (
                any(substr in model.id for substr in config.OPENAI_MODELS_TO_KEEP)
                and not any(
                    substr in model.id for substr in config.OPENAI_MODELS_TO_IGNORE
                )
                and (
                    not getattr(config, "OPENAI_IGNORE_DATED_MODEL_NAMES", False)
                    or not utils.contains_date(model.id)
                )
            ):
                models.append([model.id, model.created])

        models = sorted(models, key=lambda x: x[1])
        provided_models = []
        for model in models:
            provided_models.append(model[0])
    else:
        platform_config = config.THIRD_PARTY_PLATFORMS[config.CHA_CURRENT_PLATFORM_NAME]
        provided_models = platforms.get_platform_model_list(
            url=platform_config["models"]["url"],
            headers=platform_config["models"]["headers"],
            models_info=platform_config["models"],
        )

    if not provided_models:
        print(colors.red("No models available to select"))
        return None

    fzf_prompt = f"Select a {config.CHA_CURRENT_PLATFORM_NAME.upper()} model: "
    try:
        selected_model = utils.run_fzf_ssh_safe(
            ["fzf", "--reverse", "--height=40%", "--border", f"--prompt={fzf_prompt}"],
            "\n".join(provided_models),
        )
        return selected_model if selected_model else None
    except (subprocess.CalledProcessError, subprocess.SubprocessError):
        return None


def chatbot(selected_model, print_title=True, filepath=None, content_string=None):
    global CURRENT_CHAT_HISTORY

    reasoning_model = utils.is_slow_model(selected_model)

    auto_scrape_detection_mode = False

    # o1 models don't accept system prompts
    if len(CURRENT_CHAT_HISTORY) > 1:
        messages = []
        if not reasoning_model:
            # The first item is the initial prompt.
            if CURRENT_CHAT_HISTORY and CURRENT_CHAT_HISTORY[0].get("user"):
                messages.append(
                    {"role": "user", "content": CURRENT_CHAT_HISTORY[0]["user"]}
                )

        for item in CURRENT_CHAT_HISTORY[1:]:
            if item.get("user"):
                messages.append({"role": "user", "content": item["user"]})
            if item.get("bot"):
                messages.append({"role": "assistant", "content": item["bot"]})
    else:
        messages = (
            []
            if reasoning_model
            else [{"role": "user", "content": config.INITIAL_PROMPT}]
        )
    multi_line_input = False

    if filepath or content_string:
        if filepath:
            if "/" not in filepath:
                filepath = os.path.join(os.getcwd(), filepath)

            if not os.path.exists(filepath):
                print(colors.red(f"File does not exist {filepath}"))
                return

            print(
                colors.yellow(
                    colors.underline(
                        f"Feeding the following file content to {selected_model}:"
                    )
                )
            )
            print(colors.yellow(f"{filepath}"))
            print()

            try:
                loading.start_loading("Loading", "rectangles")
                content = utils.load_most_files(
                    client=get_current_chat_client(),
                    file_path=filepath,
                    model_name=config.CHA_DEFAULT_IMAGE_MODEL,
                )
            except:
                raise Exception(f"Failed to load file {filepath}")
            finally:
                loading.stop_loading()
        else:
            content = content_string

        messages.append({"role": "user", "content": content})
        single_response = True

    else:
        # interactive mode
        if print_title:
            title_print(selected_model)
        single_response = False

    # main loop for chatting
    while True:
        if not single_response:
            user_input_string = colors.blue("User: ")

            if multi_line_input:
                user_input_string = colors.red("[M] ") + colors.blue("User: ")

            if auto_scrape_detection_mode:
                user_input_string = colors.yellow("[S] ") + colors.blue("User: ")

            message = utils.safe_input(user_input_string).rstrip("\n")

            # print help - handle this first so selected aliases can be processed by other handlers
            if message.strip().lower() == config.HELP_PRINT_OPTIONS_KEY.lower():
                selected_alias = interactive_help(selected_model)
                if selected_alias:
                    # execute the selected alias by treating it as a new message
                    message = selected_alias
                    # continue processing with the selected alias
                else:
                    continue

            if message.strip() == config.BACKTRACK_HISTORY_KEY:
                if len(CURRENT_CHAT_HISTORY) <= 1:
                    print(colors.yellow("No chat history to backtrack through"))
                    continue

                selected_indices = backtrack_history(CURRENT_CHAT_HISTORY)
                if selected_indices is not None:
                    original_length = len(CURRENT_CHAT_HISTORY)
                    selected_indices = sorted(selected_indices, reverse=True)

                    for index in selected_indices:
                        if 1 <= index < len(CURRENT_CHAT_HISTORY):
                            CURRENT_CHAT_HISTORY.pop(index)

                    messages.clear()
                    if not reasoning_model:
                        if CURRENT_CHAT_HISTORY and CURRENT_CHAT_HISTORY[0].get("user"):
                            messages.append(
                                {
                                    "role": "user",
                                    "content": CURRENT_CHAT_HISTORY[0]["user"],
                                }
                            )

                    for item in CURRENT_CHAT_HISTORY[1:]:
                        if item.get("user"):
                            messages.append({"role": "user", "content": item["user"]})
                        if item.get("bot"):
                            messages.append(
                                {"role": "assistant", "content": item["bot"]}
                            )

                    num_removed = original_length - len(CURRENT_CHAT_HISTORY)
                    if num_removed > 0:
                        chat_word = "chat" if num_removed == 1 else "chats"
                        indices_str = ", ".join(
                            str(i) for i in sorted(selected_indices)
                        )
                        print(colors.red(f"Removed {chat_word}: {indices_str}"))
                continue

            if message.startswith(config.CHANGE_DIRECTORY_ALIAS):
                try:
                    from cha import nav

                    # store current directory to check if it actually changes
                    current_dir = os.getcwd()

                    # extract directory path if provided
                    dir_path = None
                    parts = message.split(maxsplit=1)
                    if len(parts) > 1:
                        dir_path = parts[1].strip()

                    # navigate to new directory
                    new_dir = nav.fzf_directory_navigation(dir_path)
                    if new_dir and os.path.isdir(new_dir):
                        os.chdir(new_dir)
                        # only print success message if directory actually changed
                        if os.getcwd() != current_dir:
                            print(colors.green(f"Changed directory to: {new_dir}"))
                            # track visited directory for exit display
                            if new_dir not in VISITED_DIRECTORIES:
                                VISITED_DIRECTORIES.append(new_dir)
                    # don't print error message if user simply cancelled/exited
                except Exception as e:
                    print(colors.red(f"Error changing directory: {e}"))
                continue

            if message.strip().startswith(config.RUN_EDITOR_ALIAS):
                editor_message = None
                if len(message.split(" ")) > 1:
                    editor_message = message.replace(
                        config.RUN_EDITOR_ALIAS, ""
                    ).strip()

                try:
                    from cha import editor

                    editor.call_editor(
                        client=get_current_chat_client(),
                        initial_prompt=editor_message,
                        model_name=selected_model,
                    )
                except (KeyboardInterrupt, EOFError):
                    continue

                continue

            if message == config.TEXT_EDITOR_INPUT_MODE:
                editor_content = utils.check_terminal_editors_and_edit()
                if editor_content is None:
                    print(colors.red(f"No text editor available or editing cancelled"))
                    continue
                message = editor_content
                if len(message) == 0:
                    continue
                for line in message.rstrip("\n").split("\n"):
                    print(colors.blue(">"), line)

            if message.startswith(config.SWITCH_MODEL_TEXT):
                parts = message.strip().split(maxsplit=1)
                if len(parts) == 1:
                    new_selected_model = list_models()
                    if new_selected_model:
                        selected_model = new_selected_model
                        print(colors.magenta(f"Switched to model: {selected_model}"))
                        reasoning_model = utils.is_slow_model(selected_model)

                else:
                    # note: unsafe but faster direct model switching
                    selected_model = parts[1].strip()
                    print(colors.magenta(f"Switched to model: {selected_model}"))
                    reasoning_model = utils.is_slow_model(selected_model)

                continue

            if message.startswith(config.SWITCH_PLATFORM_TEXT):
                parts = message.strip().split(maxsplit=1)
                if len(parts) == 1:
                    from cha import platforms

                    try:
                        platform_values = platforms.auto_select_a_platform()
                        if platform_values:
                            API_KEY_NAME = platform_values["env_name"]
                            BASE_URL_VALUE = platform_values["base_url"]
                            selected_model = platform_values["picked_model"]
                            platform_name = platform_values["platform_name"]

                            API_KEY_VALUE = API_KEY_NAME
                            if API_KEY_VALUE in os.environ:
                                API_KEY_VALUE = os.environ.get(API_KEY_NAME)

                            set_current_chat_client(API_KEY_VALUE, BASE_URL_VALUE)
                            config.CHA_CURRENT_PLATFORM_NAME = platform_name
                            reasoning_model = utils.is_slow_model(selected_model)

                            print(
                                colors.magenta(f"Switched to platform: {platform_name}")
                            )
                            print(colors.magenta(f"Using model: {selected_model}"))
                        else:
                            print(colors.red("No platform selected"))
                    except Exception as e:
                        print(colors.red(f"Failed to switch platform: {e}"))
                else:
                    try:
                        from cha import platforms

                        platform_args = parts[1].strip()
                        platform_values = platforms.auto_select_a_platform(
                            platform_key=(
                                platform_args.split("|")[0]
                                if "|" in platform_args
                                else platform_args
                            ),
                            model_name=(
                                platform_args.split("|")[1]
                                if "|" in platform_args
                                else None
                            ),
                        )

                        if platform_values:
                            API_KEY_NAME = platform_values["env_name"]
                            BASE_URL_VALUE = platform_values["base_url"]
                            selected_model = platform_values["picked_model"]
                            platform_name = platform_values["platform_name"]

                            API_KEY_VALUE = API_KEY_NAME
                            if API_KEY_VALUE in os.environ:
                                API_KEY_VALUE = os.environ.get(API_KEY_NAME)

                            set_current_chat_client(API_KEY_VALUE, BASE_URL_VALUE)
                            config.CHA_CURRENT_PLATFORM_NAME = platform_name
                            reasoning_model = utils.is_slow_model(selected_model)

                            print(
                                colors.magenta(f"Switched to platform: {platform_name}")
                            )
                            print(colors.magenta(f"Using model: {selected_model}"))
                        else:
                            print(colors.red("Failed to switch platform"))
                    except Exception as e:
                        print(colors.red(f"Failed to switch platform: {e}"))

                continue

            if message == config.MULTI_LINE_MODE_TEXT:
                multi_line_input = True
                continue

            elif message.replace(" ", "").lower() == config.EXIT_STRING_KEY.lower():
                break

            elif message.strip() == config.RECORD_AUDIO_ALIAS:
                try:
                    from cha import recording

                    recorded_text = recording.record_get_text(get_current_chat_client())
                    if recorded_text:
                        print(colors.blue("User:"), colors.white(recorded_text))
                        message = recorded_text
                        messages.append({"role": "user", "content": message})
                    else:
                        continue
                except Exception as e:
                    print(colors.red(f"Recording failed: {e}"))
                    continue

            elif os.path.isdir(config.LOCAL_CHA_CONFIG_HISTORY_DIR) and (
                message.strip().lower() == config.LOAD_HISTORY_TRIGGER
                or message.strip().lower().startswith(config.LOAD_HISTORY_TRIGGER + " ")
            ):
                from cha import local

                try:
                    parts = (
                        message.strip().lower().split(config.LOAD_HISTORY_TRIGGER, 1)
                    )
                    search_mode_arg = parts[1].strip() if len(parts) > 1 else "fuzzy"
                    exact_mode = search_mode_arg == "exact"

                    hs_output = local.browse_and_select_history_file(
                        exact_mode=exact_mode
                    )
                    if not hs_output or not isinstance(hs_output, dict):
                        continue

                    selected_path = hs_output.get("path")
                    chat_msgs = hs_output.get("chat")

                    if not selected_path or not chat_msgs:
                        continue

                    print(colors.magenta(selected_path))
                    local.print_history_browse_and_select_history_file(chat_msgs)

                    CURRENT_CHAT_HISTORY.clear()
                    CURRENT_CHAT_HISTORY.extend(chat_msgs)

                    messages.clear()
                    if not reasoning_model:
                        messages.append(
                            {"role": "user", "content": config.INITIAL_PROMPT}
                        )

                    for item in chat_msgs[1:]:
                        if item.get("user"):
                            messages.append({"role": "user", "content": item["user"]})
                        if item.get("bot"):
                            messages.append(
                                {"role": "assistant", "content": item["bot"]}
                            )
                except (KeyboardInterrupt, EOFError):
                    print()
                except Exception as e:
                    if config.CHA_DEBUG_MODE:
                        print(colors.red(f"Error loading history: {e}"))
                continue

            if message.startswith(config.PICK_AND_RUN_A_SHELL_OPTION):
                # Extract command if provided
                command = None
                parts = message.split(maxsplit=1)
                if len(parts) > 1:
                    command = parts[1].strip()
                utils.run_a_shell(command)
                continue

            elif message.replace(" ", "").lower() == config.CLEAR_HISTORY_TEXT.lower():
                messages = (
                    []
                    if reasoning_model
                    else [{"role": "user", "content": config.INITIAL_PROMPT}]
                )
                print(colors.yellow("Chat history cleared"))
                continue

            if multi_line_input:
                # keep appending lines until user types the MULTI_LINE_SEND text
                if message.lower() == config.MULTI_LINE_SEND.lower():
                    multi_line_input = False
                    continue
                message_lines = [message]
                while True:
                    line = utils.safe_input("").rstrip("\n")
                    if line.lower() == config.MULTI_LINE_SEND.lower():
                        break
                    message_lines.append(line)
                message = "\n".join(message_lines)
                multi_line_input = False

            # NOTE: handle logic for external tool calling and processing
            exist_early_due_to_tool_calling_config = False
            external_tools = config.get_external_tools_execute()
            for tool_data in external_tools:
                alias = tool_data["alias"]
                show_loading_animation = tool_data.get("show_loading_animation", True)
                if message.strip().startswith(alias):
                    from cha import local

                    if show_loading_animation:
                        loading.start_loading("Running External Tool", "dots")

                    tool_call_output = local.execute_tool(
                        tool_data=tool_data,
                        chat_history=messages,
                        piped_question=message.replace(alias, "").strip(),
                    )
                    if tool_call_output["error"] != None:
                        print(
                            colors.red(
                                f"Failed to run tool '{alias}' due to: {tool_call_output['error']}"
                            )
                        )
                        exist_early_due_to_tool_calling_config = True
                    else:
                        tool_result = tool_call_output["result"]
                        if len(str(tool_result)) > 0:
                            messages.append(
                                {"role": "assistant", "content": tool_result}
                            )
                            CURRENT_CHAT_HISTORY.append(
                                {
                                    "time": time.time(),
                                    "user": message,
                                    "bot": tool_result,
                                    "platform": config.CHA_CURRENT_PLATFORM_NAME,
                                    "model": selected_model,
                                }
                            )
                        message = tool_result
                        exist_early_due_to_tool_calling_config = not tool_call_output[
                            "continue"
                        ]

                    if show_loading_animation:
                        loading.stop_loading()
                    break

            if exist_early_due_to_tool_calling_config:
                continue

            if message.strip().startswith(config.ENABLE_OR_DISABLE_AUTO_SD):
                if (
                    auto_scrape_detection_mode == False
                    and utils.number_of_urls(message) > 0
                ):
                    loading.start_loading("Scraping URL(s)", "basic")
                    from cha import scraper

                    try:
                        message = scraper.scraped_prompt(message)
                    except:
                        message = None
                    finally:
                        loading.stop_loading()

                    if message != None:
                        print(colors.green(f"Scraped content added to chat history"))
                        messages.append({"role": "user", "content": message})
                    continue
                else:
                    auto_scrape_detection_mode = not auto_scrape_detection_mode
                    continue

            # save chat history to a JSON file or text file
            if message.strip().startswith(config.SAVE_CHAT_HISTORY):
                args = message.strip().lower().split()

                # Check if user wants text export
                if len(args) > 1 and args[1] in ["text", "txt"]:
                    # Export as text file (like old !ew command)
                    if len(CURRENT_CHAT_HISTORY) > 1:
                        chat_filename = (
                            f"cha_{str(uuid.uuid4()).replace('-', '')[:8]}.txt"
                        )
                        chat_content = ""

                        for history_item in CURRENT_CHAT_HISTORY[1:]:
                            timestamp = time.strftime(
                                "%Y-%m-%d %H:%M:%S",
                                time.localtime(history_item["time"]),
                            )
                            platform = history_item.get("platform", "unknown")
                            model = history_item.get("model", "unknown")
                            platform_info = f"[{platform}:{model}]"

                            if history_item.get("user"):
                                chat_content += f"[{timestamp}] {platform_info} User:\n{history_item['user']}\n\n"

                            if history_item.get("bot"):
                                chat_content += f"[{timestamp}] {platform_info} Bot:\n{history_item['bot']}\n\n"

                        try:
                            with open(chat_filename, "w", encoding="utf-8") as f:
                                f.write(chat_content.strip())
                            print(
                                colors.green(
                                    f"Chat history exported to {chat_filename}"
                                )
                            )
                        except Exception as e:
                            print(colors.red(f"Failed to export chat history: {e}"))
                    else:
                        print(colors.yellow("No chat history to export"))
                else:
                    # Default behavior: save as JSON
                    cha_filepath = f"cha_{int(time.time())}.json"
                    utils.write_json(cha_filepath, CURRENT_CHAT_HISTORY)
                    print(colors.red(f"Saved current chat history to {cha_filepath}"))
                continue

            if message.strip().startswith(config.EXPORT_FILES_IN_OUTPUT_KEY):
                args = message.strip().lower().split()

                export_all = "all" in args
                force_single = "single" in args

                print(colors.green(f"Created following file(s):"))

                if export_all:
                    if len(CURRENT_CHAT_HISTORY) > 1:
                        for history_item in CURRENT_CHAT_HISTORY[1:]:
                            if history_item.get("bot"):
                                utils.export_file_logic(
                                    history_item["bot"], force_single
                                )
                    else:
                        print(colors.yellow("No history to export"))
                else:
                    if len(CURRENT_CHAT_HISTORY) > 1:
                        last_bot_message = CURRENT_CHAT_HISTORY[-1].get("bot")
                        if last_bot_message:
                            utils.export_file_logic(last_bot_message, force_single)
                        else:
                            print(
                                colors.yellow("Last message has no content to export")
                            )
                    else:
                        print(colors.yellow("No message to export"))
                continue

            # prompt user to load files (simple mode)
            if message == config.LOAD_MESSAGE_CONTENT:
                from cha import traverse

                message = traverse.msg_content_load(
                    get_current_chat_client(), simple=True
                )
                if message != None:
                    messages.append({"role": "user", "content": message})
                continue

            # prompt user to load files (advanced mode)
            if message == config.LOAD_MESSAGE_CONTENT_ADVANCED:
                from cha import traverse

                message = traverse.msg_content_load(
                    get_current_chat_client(), simple=False
                )
                if message != None:
                    messages.append({"role": "user", "content": message})
                continue

            if message.startswith(config.USE_CODE_DUMP):
                try:
                    from cha import codedump

                    dir_path = message.replace(config.USE_CODE_DUMP, "").replace(
                        " ", ""
                    )
                    if "/" not in str(dir_path):
                        dir_path = None
                    try:
                        report = codedump.code_dump(dir_full_path=dir_path)
                    except SystemExit:
                        report = None
                        pass
                    if report != None:
                        messages.append({"role": "user", "content": report})
                    continue
                except (KeyboardInterrupt, EOFError):
                    print()
                    continue

            # check for URLs -> scraping
            if auto_scrape_detection_mode:
                if utils.number_of_urls(message) > 0:
                    loading.start_loading("Scraping URLs", "star")
                    from cha import scraper

                    try:
                        message = scraper.scraped_prompt(message)
                    except:
                        message = None
                    finally:
                        loading.stop_loading()

                    if message != None:
                        print(colors.green(f"Scraped content added to chat history"))
                        messages.append({"role": "user", "content": message})
                    continue

            # check for an answer-search command
            if message.startswith(config.RUN_ANSWER_FEATURE):
                quick_browse_mode = False
                if len(message) > len(config.RUN_ANSWER_FEATURE):
                    answer_prompt_draft = message[
                        len(config.RUN_ANSWER_FEATURE) :
                    ].strip()
                    if len(answer_prompt_draft) > 10:
                        quick_browse_mode = True

                from cha import answer

                if quick_browse_mode:
                    message = message.replace(config.RUN_ANSWER_FEATURE, "").strip()
                    new_message = answer.quick_search(user_input=message)
                    if new_message == None:
                        print(colors.red(f"Failed to do a quick web search"))
                        continue
                    message = new_message
                else:
                    try:
                        message = answer.answer_search(
                            client=get_current_chat_client(),
                            prompt=None,
                            user_input_mode=True,
                        )

                        messages.append({"role": "user", "content": message})

                        CURRENT_CHAT_HISTORY.append(
                            {
                                "time": time.time(),
                                "user": "",
                                "bot": message,
                                "platform": config.CHA_CURRENT_PLATFORM_NAME,
                                "model": selected_model,
                            }
                        )
                    except (KeyboardInterrupt, EOFError, SystemExit):
                        pass

                    continue

            # skip if user typed something blank
            if len("".join(str(message)).split()) == 0:
                if auto_scrape_detection_mode == True:
                    auto_scrape_detection_mode = False
                continue

            if message.strip().endswith(config.SKIP_SEND_TEXT):
                continue

            # add user's message
            messages.append({"role": "user", "content": message})

        # prepare a chat record for local usage
        obj_chat_history = {
            "time": time.time(),
            "user": messages[-1]["content"],
            "bot": "",
            "platform": config.CHA_CURRENT_PLATFORM_NAME,
            "model": selected_model,
        }

        # attempt to send the user's prompt to the selected model
        try:
            if reasoning_model:
                loading.start_loading("Thinking", "braille")
                response = get_current_chat_client().chat.completions.create(
                    model=selected_model, messages=messages
                )
                loading.stop_loading()
                full_response = response.choices[0].message.content
                print(colors.green(full_response))
                obj_chat_history["bot"] = full_response

            else:
                response = get_current_chat_client().chat.completions.create(
                    model=selected_model, messages=messages, stream=True
                )
                full_response = ""
                try:
                    error_count = 0
                    for chunk in response:
                        try:
                            chunk_message = chunk.choices[0].delta.content
                        except:
                            error_count += 1
                            if error_count > config.CHA_STREAMING_ERROR_LIMIT:
                                break
                            pass
                        if chunk_message:
                            sys.stdout.write(colors.green(chunk_message))
                            full_response += chunk_message
                            obj_chat_history["bot"] += chunk_message
                            sys.stdout.flush()
                except (KeyboardInterrupt, EOFError):
                    full_response += " [cancelled]"
                    obj_chat_history["bot"] += " [cancelled]"

            if full_response:
                messages.append({"role": "assistant", "content": full_response})
                if not reasoning_model and not full_response.endswith("\n"):
                    sys.stdout.write("\n")
                    sys.stdout.flush()

        except (KeyboardInterrupt, EOFError):
            loading.stop_loading()
            if messages and messages[-1]["role"] == "user":
                messages.pop()
            continue
        except Exception as e:
            loading.stop_loading()
            print(colors.red(f"Error during chat: {e}"))
            break

        CURRENT_CHAT_HISTORY.append(obj_chat_history)

        if single_response:
            break


def cli():
    global CURRENT_CHAT_HISTORY

    save_chat_state = True
    args = None

    try:
        parser = argparse.ArgumentParser(
            description="A command-line tool for interacting with AI models from multiple providers.",
            add_help=False,
        )
        parser.add_argument(
            "-h",
            "--help",
            action="help",
            default=argparse.SUPPRESS,
            help="Show this help message and exit.",
        )
        parser.add_argument(
            "-l",
            "--load",
            dest="file",
            help="Load a file to send to the model (interactive: !l)",
        )
        parser.add_argument(
            "-a",
            "--answer",
            dest="answer_search",
            action="store_true",
            help="Run answer search (interactive: !s)",
        )
        parser.add_argument(
            "-t",
            "--ide",
            dest="integrated_dev_env",
            action="store_true",
            help="Use a terminal text editor for input (interactive: !t)",
        )
        parser.add_argument(
            "-m",
            "--model",
            help="Switch model (interactive: !m)",
            default=config.CHA_DEFAULT_MODEL,
        )
        parser.add_argument(
            "-p",
            "--platform",
            nargs="?",
            const=True,
            help="Switch platform (interactive: !p)",
        )
        parser.add_argument(
            "-d",
            "--codedump",
            dest="code_dump",
            nargs="?",
            const=True,
            help="Codedump a directory (interactive: !d)",
        )
        parser.add_argument(
            "-e",
            "--export",
            dest="export_parsed_text",
            action="store_true",
            help="Export code blocks from the last response (interactive: !e)",
        )
        parser.add_argument(
            "-x",
            "--shell",
            dest="shell_command",
            help="Execute a shell command (interactive: !x)",
        )
        parser.add_argument(
            "-hs",
            "--history",
            dest="history_search",
            nargs="?",
            const="fuzzy",
            choices=["fuzzy", "exact"],
            help="Search history. 'fuzzy' (default), 'exact' for exact. (interactive: !hs)",
        )
        parser.add_argument(
            "-r",
            "--record",
            dest="record_voice",
            action="store_true",
            help="Record voice prompt (interactive: !r)",
        )
        parser.add_argument(
            "-v",
            "--editor",
            dest="editor",
            nargs="?",
            const=True,
            help="Run the interactive editor (interactive: !v)",
        )
        parser.add_argument(
            "-sm",
            "--select-model",
            dest="select_model",
            action="store_true",
            help="Select a model from a list",
        )
        parser.add_argument(
            "-ct",
            "--tokens",
            dest="token_count",
            action="store_true",
            help="Count tokens for the input",
        )
        parser.add_argument(
            "-ocr",
            "--ocr",
            help="Extract text from a file using OCR",
        )
        parser.add_argument(
            "-i",
            "--init",
            action="store_true",
            dest="init",
            help="Initialize cha config directory",
        )
        parser.add_argument(
            "-P",
            "--private",
            action="store_true",
            dest="private",
            help="Enable private mode (no history saved)",
        )
        parser.add_argument(
            "-V",
            "--version",
            action="store_true",
            dest="version",
            help="Show version information",
        )
        parser.add_argument(
            "-lh",
            "--load-history",
            dest="load_history_file",
            help="Load a chat history from a file.",
        )
        parser.add_argument(
            "string",
            nargs="*",
            help="Non-interactive mode, feed a string into the model",
        )

        args = parser.parse_args()

        if args.load_history_file:
            history_file_path = args.load_history_file
            if not os.path.isabs(history_file_path) and os.path.isdir(
                config.LOCAL_CHA_CONFIG_HISTORY_DIR
            ):
                history_file_path = os.path.join(
                    config.LOCAL_CHA_CONFIG_HISTORY_DIR, history_file_path
                )

            if not os.path.exists(history_file_path):
                print(colors.red(f"History file not found"))
                return

            try:
                with open(history_file_path, "r", encoding="utf-8") as f:
                    history_data = json.load(f)

                chat_history = None
                if isinstance(history_data, dict) and "chat" in history_data:
                    chat_history = history_data["chat"]
                elif isinstance(history_data, list):
                    chat_history = history_data

                if chat_history is not None and isinstance(chat_history, list):
                    if chat_history and not all(
                        isinstance(item, dict) for item in chat_history
                    ):
                        raise ValueError(
                            "Invalid history format: must be a list of objects."
                        )

                    CURRENT_CHAT_HISTORY.clear()
                    CURRENT_CHAT_HISTORY.extend(chat_history)
                    if not CURRENT_CHAT_HISTORY:
                        CURRENT_CHAT_HISTORY.append(
                            {
                                "time": time.time(),
                                "user": config.INITIAL_PROMPT,
                                "bot": "",
                                "platform": config.CHA_CURRENT_PLATFORM_NAME,
                                "model": config.CHA_DEFAULT_MODEL,
                            }
                        )

                    from cha import local

                    print(colors.magenta(history_file_path))
                    local.print_history_browse_and_select_history_file(
                        CURRENT_CHAT_HISTORY
                    )
                else:
                    raise ValueError("Invalid history format.")
            except (json.JSONDecodeError, ValueError) as e:
                print(
                    colors.red(
                        f"Error loading history file '{args.load_history_file}': {e}"
                    )
                )
                return

        if args.shell_command:
            utils.run_a_shell(args.shell_command)
            return

        if args.version:
            try:
                from importlib.metadata import version

                print(f"{version('cha')} (Cha)")
            except:
                print("?")
            return

        if args.init:
            from cha import local

            output = local.setup_cha_config_dir()
            if output == False:
                print(colors.red(f"Failed to create .cha/ local config setup"))
            elif output == True:
                print(colors.green(f"Successfully created .cha/ local config setup"))
            else:
                print(
                    colors.red(
                        f"Failed to create .cha/ local config setup due to an unexpected error"
                    )
                )
            return

        if args.history_search:
            try:
                from cha import local

                hs_output = local.browse_and_select_history_file(
                    exact_mode=(args.history_search == "exact")
                )
                if hs_output and isinstance(hs_output, dict):
                    selected_path = hs_output.get("path")
                    chat_msgs = hs_output.get("chat")
                    if selected_path and chat_msgs:
                        print(colors.magenta(selected_path))
                        local.print_history_browse_and_select_history_file(chat_msgs)
            except (KeyboardInterrupt, EOFError):
                print()
            except Exception as e:
                print(colors.red(f"Failed to search history: {e}"))
            return

        if args.editor:
            from cha import editor

            editor.run_editor(
                client=get_current_chat_client(),
                model_name=args.model,
                file_path=args.editor if isinstance(args.editor, str) else None,
            )
            return

        if args.private:
            save_chat_state = False

        if args.code_dump == True:
            from cha import codedump

            codedump.code_dump(save_file_to_current_dir=True)
            return

        if args.ocr != None:
            content = None

            if utils.number_of_urls(str(args.ocr)) > 0:
                from cha import scraper

                detected_urls = scraper.extract_urls(str(args.ocr))

                for i in range(len(detected_urls)):
                    detected_urls[i] = str(detected_urls[i]).replace("\\", "")
                content = scraper.get_all_htmls(detected_urls)
            else:
                content = utils.act_as_ocr(
                    client=get_current_chat_client(),
                    filepath=str(args.ocr),
                    prompt=None,
                )

            if content == None:
                print(colors.red(f"Failed to load file due to an error"))
            elif type(content) == dict:
                print(json.dumps(content, indent=4))
            else:
                print(content)
            return

        if args.answer_search == True:
            try:
                from cha import answer

                output = answer.answer_search(
                    client=get_current_chat_client(),
                    prompt=None,
                    user_input_mode=True,
                )
            except (KeyboardInterrupt, EOFError, SystemExit):
                return None

            save_chat_state = False
            if output is None:
                raise Exception("Answer search existed with None")

            return

        title_print_value = config.CHA_DEFAULT_SHOW_PRINT_TITLE
        selected_model = args.model

        if args.record_voice:
            try:
                from cha import recording

                recorded_text = recording.record_get_text(get_current_chat_client())
                if recorded_text:
                    print(colors.blue("User:"), colors.white(recorded_text))
                    chatbot(
                        selected_model, title_print_value, content_string=recorded_text
                    )
                else:
                    print(colors.red("No audio recorded"))
            except Exception as e:
                print(colors.red(f"Recording failed: {e}"))
            return

        if args.platform or config.CHA_CURRENT_PLATFORM_NAME != "openai":
            platform_arg = args.platform
            if not platform_arg and config.CHA_CURRENT_PLATFORM_NAME != "openai":
                platform_arg = config.CHA_CURRENT_PLATFORM_NAME

            try:
                from cha import platforms

                API_KEY_NAME = None
                BASE_URL_VALUE = None
                platform_name = None

                if (
                    isinstance(platform_arg, str)
                    and "|" in platform_arg
                    and "http" in platform_arg
                ):
                    parts = platform_arg.split("|", 1)
                    BASE_URL_VALUE = parts[0]
                    API_KEY_NAME = parts[1]
                else:
                    platform_model_name = None
                    if isinstance(platform_arg, str):
                        if "|" in platform_arg:
                            parts = platform_arg.split("|", 1)
                            platform_name = parts[0]
                            platform_model_name = parts[1]
                        else:
                            platform_name = platform_arg

                    if args.model and args.model != config.CHA_DEFAULT_MODEL:
                        platform_model_name = args.model

                    platform_values = platforms.auto_select_a_platform(
                        platform_key=platform_name,
                        model_name=platform_model_name,
                    )

                    if not platform_values:
                        # user cancelled platform selection - exit silently
                        return

                    API_KEY_NAME = platform_values.get("env_name")
                    BASE_URL_VALUE = platform_values.get("base_url")
                    selected_model = platform_values.get("picked_model")
                    platform_name = platform_values.get("platform_name")

                if not API_KEY_NAME or not BASE_URL_VALUE:
                    raise Exception(
                        "Missing API key or base URL for the selected platform."
                    )

                API_KEY_VALUE = os.environ.get(API_KEY_NAME, API_KEY_NAME)
                set_current_chat_client(API_KEY_VALUE, BASE_URL_VALUE)

                if not platform_name:
                    for p_name, p_data in config.THIRD_PARTY_PLATFORMS.items():
                        if p_data["base_url"] in BASE_URL_VALUE:
                            platform_name = p_name
                            break

                if platform_name:
                    config.CHA_CURRENT_PLATFORM_NAME = platform_name

                if config.CHA_DEFAULT_SHOW_PRINT_TITLE:
                    print(
                        colors.magenta(
                            f"Platform switched to {platform_name or BASE_URL_VALUE}"
                        )
                    )

            except Exception as e:
                save_chat_state = False
                raise Exception(f"Failed to switch platform due to {e}")

        if args.select_model:
            new_selected_model = list_models()
            if new_selected_model:
                selected_model = new_selected_model
            else:
                # user cancelled model selection - exit silently
                return

        if args.token_count:
            save_chat_state = False

            text, content_mode = None, None

            if args.file:
                content_mode = "FILE"
                text = utils.load_most_files(args.file, get_current_chat_client())
            elif args.string:
                content_mode = "STRING"
                text = " ".join(args.string)
            elif not sys.stdin.isatty():
                content_mode = "PIPE"
                text = sys.stdin.read()

            if text is None:
                print(
                    colors.red(
                        "Please provide input text, a filepath, or pipe in content for token counting"
                    )
                )
                return

            try:
                token_count = utils.count_tokens(text, selected_model)
                if token_count is None:
                    raise Exception("Failed to calculate token count")
                print(colors.green("Content Type:"), content_mode)
                print(colors.green("Selected Model:"), args.model)
                print(colors.green("Text Length:"), len(text), "chars")
                print(colors.green("Token Count:"), token_count, "tokens")
                return
            except Exception as e:
                raise Exception(f"Error counting tokens: {e}")

        input_mode = "interactive"
        processed_input_for_chatbot = (
            None  # content string or None if using filepath/interactive
        )

        # check for piped input first
        if not sys.stdin.isatty():
            piped_content = sys.stdin.read()
            if args.string:
                # combine piped content and command-line string args
                processed_input_for_chatbot = (
                    f"{piped_content}\n\n---\n\n{' '.join(args.string)}"
                )
                input_mode = "pipe_with_args"
            else:
                # use only piped content
                processed_input_for_chatbot = piped_content
                input_mode = "pipe_only"
        elif args.file:
            input_mode = "file"
        elif args.string:
            processed_input_for_chatbot = " ".join(args.string)
            input_mode = "string_args"
        elif args.integrated_dev_env:
            # use IDE input only if not piped, no file, no string args
            editor_content = utils.check_terminal_editors_and_edit()
            if editor_content is None:
                save_chat_state = False
                raise Exception("No text editor available or editing cancelled")
            processed_input_for_chatbot = editor_content
            input_mode = "ide"

        # call chatbot based on input mode
        if input_mode in ["pipe_with_args", "pipe_only", "string_args", "ide"]:
            chatbot(
                selected_model,
                title_print_value,
                content_string=processed_input_for_chatbot,
            )
        elif input_mode == "file":
            chatbot(selected_model, title_print_value, filepath=args.file)
        else:
            chatbot(selected_model=selected_model, print_title=title_print_value)

        # handle export logic only if export flag is set and it wasn't an interactive session
        if args.export_parsed_text and input_mode != "interactive":
            print()
            # check if there's history to export from (chatbot appends even in non-interactive modes)
            # the first entry is the initial prompt, so we need at least 2 entries for a response.
            if CURRENT_CHAT_HISTORY and len(CURRENT_CHAT_HISTORY) > 1:
                utils.export_file_logic(CURRENT_CHAT_HISTORY[-1]["bot"])
            else:
                print(colors.yellow("No chat response found to export files from"))

    except (KeyboardInterrupt, EOFError):
        print()
    except Exception as err:
        if config.CHA_DEBUG_MODE:
            print(colors.red(str(traceback.format_exc())))
        elif str(err):
            err_msg = f"{err}"
            if save_chat_state:
                # NOTE: a newline is needed to prevent text overlap during streaming cancellation
                err_msg = "\n" + err_msg
            print(colors.red(err_msg))
        else:
            print(colors.red("Exited unexpectedly"))
    except SystemExit:
        # account for when main input function exists
        pass

    # save chat locally if desired
    try:
        if (
            config.CHA_LOCAL_SAVE_ALL_CHA_CHATS == True
            and save_chat_state == True
            and len(CURRENT_CHAT_HISTORY) > 1
            and os.path.exists(config.LOCAL_CHA_CONFIG_HISTORY_DIR)
        ):
            from datetime import datetime, timezone
            from importlib.metadata import version
            import uuid

            try:
                version_id = str(version("cha"))
            except:
                version_id = "?"

            epoch_time_seconds = time.time()
            utc_time_stamp = f"{datetime.now(timezone.utc)} UTC"
            file_id = str(uuid.uuid4())

            history_save = {
                "chat": CURRENT_CHAT_HISTORY,
                "id": file_id,
                "version": version_id,
                "date": {
                    "epoch": {"seconds": epoch_time_seconds},
                    "utc": utc_time_stamp,
                },
                "args": {},
                "config": utils.get_json_serializable_globals(config),
            }

            if args != None:
                history_save["args"] = vars(args)

            file_path = os.path.join(
                config.LOCAL_CHA_CONFIG_HISTORY_DIR,
                f"cha_hs_{int(epoch_time_seconds)}.json",
            )

            utils.write_json(file_path, history_save)
    except Exception as e:
        if config.CHA_DEBUG_MODE:
            print(colors.red(str(traceback.format_exc())))
        else:
            print(colors.red(f"Unexpected error well handling local logic: {str(e)}"))

    # display visited directories on exit if enabled and directories were visited
    if config.CHA_SHOW_VISITED_DIRECTORIES_ON_EXIT and VISITED_DIRECTORIES:
        formatted_dirs = format_visited_directories(VISITED_DIRECTORIES)
        print(colors.cyan(f"Visited: {formatted_dirs}"))
