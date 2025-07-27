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
HISTORY_MODIFIED = False


def format_visited_directories(directories):
    """
    Format visited directories for exit display
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
    help_options.append(f"{config.RUN_QUICK_SEARCH_FEATURE} - Quick web search")
    help_options.append(f"{config.RUN_ANSWER_FEATURE} - Deep answer search")
    help_options.append(f"{config.RECORD_AUDIO_ALIAS} - Record voice prompt")
    help_options.append(
        f"{config.VOICE_OUTPUT_ALIAS} - Read out the last response using a voice"
    )
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
    bracket_options.append(
        f"{config.EXPORT_FILES_IN_OUTPUT_KEY} - Export chat history with fzf selection"
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

            # handle multiple selections, then just print them
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


def chatbot(selected_model, print_title=True, filepath=None, content_string=None):
    global CURRENT_CHAT_HISTORY, HISTORY_MODIFIED

    output_is_piped = not sys.stdout.isatty()
    reasoning_model = utils.is_slow_model(selected_model)

    auto_scrape_detection_mode = False

    # openai's o-models don't accept system prompts
    if len(CURRENT_CHAT_HISTORY) > 1:
        messages = []
        if not reasoning_model:
            # the first item is the initial prompt.
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
                if not output_is_piped:
                    print(colors.red(f"File does not exist {filepath}"))
                return

            if not output_is_piped:
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
                if not output_is_piped:
                    loading.start_loading("Loading", "rectangles")
                content = utils.load_most_files(
                    client=get_current_chat_client(),
                    file_path=filepath,
                    model_name=config.CHA_DEFAULT_IMAGE_MODEL,
                )
            except:
                raise Exception(f"Failed to load file {filepath}")
            finally:
                if not output_is_piped:
                    loading.stop_loading()
        else:
            content = content_string

        messages.append({"role": "user", "content": content})
        single_response = True

    else:
        # interactive mode
        if print_title and not output_is_piped:
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

            # print help
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
                        HISTORY_MODIFIED = True
                        chat_word = "chat" if num_removed == 1 else "chats"
                        print(
                            colors.red(
                                f"Removed {num_removed} {chat_word} from history"
                            )
                        )
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

                    history_updated = editor.run_editor(
                        client=get_current_chat_client(),
                        model_name=selected_model,
                        file_path=editor_message,
                        chat_history=CURRENT_CHAT_HISTORY,
                    )
                    if history_updated:
                        HISTORY_MODIFIED = True
                        messages.clear()
                        if not reasoning_model:
                            if CURRENT_CHAT_HISTORY and CURRENT_CHAT_HISTORY[0].get(
                                "user"
                            ):
                                messages.append(
                                    {
                                        "role": "user",
                                        "content": CURRENT_CHAT_HISTORY[0]["user"],
                                    }
                                )
                        for item in CURRENT_CHAT_HISTORY[1:]:
                            if item.get("user"):
                                messages.append(
                                    {"role": "user", "content": item["user"]}
                                )
                            if item.get("bot"):
                                messages.append(
                                    {"role": "assistant", "content": item["bot"]}
                                )
                except (KeyboardInterrupt, EOFError):
                    continue
                except SystemExit:
                    sys.exit(0)
                except editor.InteractiveEditor.ChaAbortException:
                    sys.exit(0)
                except Exception as e:
                    print(colors.red(f"Editor error: {e}"))
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
                    new_selected_model = platforms.list_models()
                    if new_selected_model:
                        selected_model = new_selected_model
                        print(
                            f"{colors.magenta(config.CHA_CURRENT_PLATFORM_NAME)} {colors.yellow(selected_model)}"
                        )
                        reasoning_model = utils.is_slow_model(selected_model)

                else:
                    # NOTE: unsafe but faster direct model switching
                    selected_model = parts[1].strip()
                    print(
                        f"{colors.magenta(config.CHA_CURRENT_PLATFORM_NAME)} {colors.yellow(selected_model)}"
                    )
                    reasoning_model = utils.is_slow_model(selected_model)

                continue

            if message.startswith(config.SWITCH_PLATFORM_TEXT):
                parts = message.strip().split(maxsplit=1)
                if len(parts) == 1:
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
                                f"{colors.magenta(platform_name)} {colors.yellow(selected_model)}"
                            )
                        else:
                            print(colors.red("No platform selected"))
                    except Exception as e:
                        print(colors.red(f"Failed to switch platform: {e}"))
                else:
                    try:
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
                                f"{colors.magenta(platform_name)} {colors.yellow(selected_model)}"
                            )
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

            elif message.strip() == config.VOICE_OUTPUT_ALIAS:
                from cha import voice

                last_bot_response = None
                for i in range(len(CURRENT_CHAT_HISTORY) - 1, -1, -1):
                    if CURRENT_CHAT_HISTORY[i].get("bot"):
                        last_bot_response = CURRENT_CHAT_HISTORY[i]["bot"]
                        break
                if last_bot_response:
                    loading.start_loading("Speaking", "circles")
                    try:
                        voice.voice_tool(last_bot_response)
                    except Exception as e:
                        print(colors.red(f"Voice output failed: {e}"))
                    finally:
                        loading.stop_loading()
                else:
                    print(colors.yellow("No previous bot response to read."))
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
                    HISTORY_MODIFIED = False

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
                # extract command if provided
                command = None
                parts = message.split(maxsplit=1)
                if len(parts) > 1:
                    command = parts[1].strip()
                utils.run_a_shell(command)
                continue

            elif message.replace(" ", "").lower() == config.CLEAR_HISTORY_TEXT.lower():
                try:
                    confirmation = input(colors.yellow("Clear History [y/N]? "))
                    if confirmation.lower() == "y":
                        messages = (
                            []
                            if reasoning_model
                            else [{"role": "user", "content": config.INITIAL_PROMPT}]
                        )
                    else:
                        print(colors.red("Canceled clearing chat history"))
                except (KeyboardInterrupt, EOFError):
                    print()
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
                            HISTORY_MODIFIED = True
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

            if message.strip().startswith(config.EXPORT_FILES_IN_OUTPUT_KEY):
                if len(CURRENT_CHAT_HISTORY) <= 0:
                    print(colors.yellow("No chat history to export"))
                    continue

                try:
                    history_items = []
                    for i, msg in enumerate(CURRENT_CHAT_HISTORY, 0):
                        user_msg = msg.get("user", "").replace("\n", " ").strip()
                        user_msg = re.sub(r"\s+", " ", user_msg)
                        timestamp = time.strftime(
                            "%H:%M:%S", time.localtime(msg["time"])
                        )
                        history_items.append(f"[{i}] ({timestamp}) {user_msg}")

                    history_items = history_items[::-1]

                    # add special options of [ALL] at top, [ALL JSON] at bottom
                    fzf_options = (
                        [config.HELP_ALL_ALIAS]
                        + history_items
                        + [config.EXPORT_ALL_JSON_ALIAS]
                    )

                    selected_output = utils.run_fzf_ssh_safe(
                        [
                            "fzf",
                            "--reverse",
                            "--height=40%",
                            "--border",
                            "--prompt=Select chats to export as text (TAB for multi-select): ",
                            "--multi",
                        ],
                        "\n".join(fzf_options),
                    )

                    if not selected_output:
                        continue

                    selected_items = selected_output.split("\n")

                    # handle all json option
                    if any(
                        config.EXPORT_ALL_JSON_ALIAS in item for item in selected_items
                    ):
                        cha_filepath = f"cha_{int(time.time())}.json"
                        utils.write_json(cha_filepath, CURRENT_CHAT_HISTORY)
                        print(
                            colors.green(f"Exported all chat history to {cha_filepath}")
                        )
                        continue

                    # handle all option or specific selections
                    export_all = any(
                        config.HELP_ALL_ALIAS in item for item in selected_items
                    )

                    if export_all:
                        # export all chats as text
                        if len(CURRENT_CHAT_HISTORY) > 0:
                            chat_filename = (
                                f"cha_{str(uuid.uuid4()).replace('-', '')[:8]}.txt"
                            )
                            chat_content = ""

                            for history_item in CURRENT_CHAT_HISTORY:
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
                                        f"Exported all chat history to {chat_filename}"
                                    )
                                )
                            except Exception as e:
                                print(colors.red(f"Failed to export chat history: {e}"))
                        else:
                            print(colors.yellow("No chat history to export"))
                    else:
                        # export selected chats as text
                        selected_indices = []
                        for line in selected_items:
                            if line.strip():
                                index_match = re.match(r"\[(\d+)\]", line)
                                if index_match:
                                    selected_indices.append(int(index_match.group(1)))

                        if selected_indices:
                            chat_filename = (
                                f"cha_{str(uuid.uuid4()).replace('-', '')[:8]}.txt"
                            )
                            chat_content = ""

                            for index in selected_indices:
                                if 0 <= index <= len(CURRENT_CHAT_HISTORY) - 1:
                                    history_item = CURRENT_CHAT_HISTORY[index]
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
                                        f"Exported selected chats to {chat_filename}"
                                    )
                                )
                            except Exception as e:
                                print(
                                    colors.red(f"Failed to export selected chats: {e}")
                                )
                        else:
                            print(colors.yellow("No valid selections found"))

                except (subprocess.CalledProcessError, subprocess.SubprocessError):
                    print(colors.yellow("Export cancelled"))
                except Exception as e:
                    print(colors.red(f"Error during export: {e}"))
                continue

            # prompt user to load files (simple mode)
            if message == config.LOAD_MESSAGE_CONTENT:
                from cha import traverse

                message = traverse.msg_content_load(
                    get_current_chat_client(), simple=True
                )
                if message != None:
                    messages.append({"role": "user", "content": message})
                    CURRENT_CHAT_HISTORY.append(
                        {
                            "time": time.time(),
                            "user": message,
                            "bot": "",
                            "platform": config.CHA_CURRENT_PLATFORM_NAME,
                            "model": selected_model,
                        }
                    )
                    HISTORY_MODIFIED = True
                continue

            # prompt user to load files (advanced mode)
            if message == config.LOAD_MESSAGE_CONTENT_ADVANCED:
                from cha import traverse

                message = traverse.msg_content_load(
                    get_current_chat_client(), simple=False
                )
                if message != None:
                    messages.append({"role": "user", "content": message})
                    CURRENT_CHAT_HISTORY.append(
                        {
                            "time": time.time(),
                            "user": message,
                            "bot": "",
                            "platform": config.CHA_CURRENT_PLATFORM_NAME,
                            "model": selected_model,
                        }
                    )
                    HISTORY_MODIFIED = True
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
                        report, token_count = codedump.code_dump(
                            dir_full_path=dir_path, quiet=True
                        )
                    except SystemExit:
                        report, token_count = None, 0
                        pass
                    if report != None:
                        print(colors.magenta(f"{token_count} Total Tokens"))
                        compress_input = utils.safe_input(
                            colors.yellow("Compress (y/N)? ")
                        )
                        if compress_input.lower() == "y":
                            report = utils.simple_context_compression(
                                report, remove_comments=True
                            )
                            compressed_tokens = utils.count_tokens(
                                report, selected_model
                            )
                            print(colors.magenta(f"{compressed_tokens} Total Tokens"))

                        messages.append({"role": "user", "content": report})
                        CURRENT_CHAT_HISTORY.append(
                            {
                                "time": time.time(),
                                "user": report,
                                "bot": "",
                                "platform": config.CHA_CURRENT_PLATFORM_NAME,
                                "model": selected_model,
                            }
                        )
                        HISTORY_MODIFIED = True
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

            # check for quick search command
            if message.startswith(config.RUN_QUICK_SEARCH_FEATURE):
                from cha import answer

                query = message.replace(config.RUN_QUICK_SEARCH_FEATURE, "").strip()
                if not query:
                    query = utils.safe_input(colors.blue("Query: "))
                    if not query:
                        continue

                new_message = answer.quick_search(user_input=query)
                if new_message == None:
                    print(colors.red(f"Failed to do a quick web search"))
                    continue
                message = new_message

            # check for deep answer-search command
            elif message.startswith(config.RUN_ANSWER_FEATURE):
                from cha import answer

                try:
                    query = message.replace(config.RUN_ANSWER_FEATURE, "").strip()
                    if query:
                        # Query provided with command
                        message = answer.answer_search(
                            client=get_current_chat_client(),
                            prompt=query,
                            user_input_mode=False,
                        )
                    else:
                        # No query provided, prompt user
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
                    HISTORY_MODIFIED = True
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
                if not output_is_piped:
                    loading.start_loading("Thinking", "braille")
                response = get_current_chat_client().chat.completions.create(
                    model=selected_model, messages=messages
                )
                if not output_is_piped:
                    loading.stop_loading()
                full_response = response.choices[0].message.content
                if output_is_piped:
                    print(full_response)
                else:
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
                            if output_is_piped:
                                sys.stdout.write(chunk_message)
                            else:
                                sys.stdout.write(colors.green(chunk_message))
                            full_response += chunk_message
                            obj_chat_history["bot"] += chunk_message
                            sys.stdout.flush()
                except (KeyboardInterrupt, EOFError):
                    full_response += " [cancelled]"
                    obj_chat_history["bot"] += " [cancelled]"

            if full_response:
                messages.append({"role": "assistant", "content": full_response})
                if (
                    not reasoning_model
                    and not full_response.endswith("\n")
                    and not output_is_piped
                ):
                    sys.stdout.write("\n")
                    sys.stdout.flush()

        except (KeyboardInterrupt, EOFError):
            if not output_is_piped:
                loading.stop_loading()
            if messages and messages[-1]["role"] == "user":
                messages.pop()
            continue
        except Exception as e:
            if not output_is_piped:
                loading.stop_loading()
                print(colors.red(f"Error during chat: {e}"))
            break

        CURRENT_CHAT_HISTORY.append(obj_chat_history)
        HISTORY_MODIFIED = True

        if single_response:
            break


def cli():
    global CURRENT_CHAT_HISTORY, HISTORY_MODIFIED

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
            help="Run deep answer search (interactive: !w)",
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
            help="Codedump a directory (interactive: !d). Options: all, stdout, compress, include:path1,path2 or combine: include:src/,stdout",
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
            "--voice",
            action="store_true",
            dest="voice_output",
            help="Read out the response from the model using a voice",
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
            "-c",
            "--continue",
            action="store_true",
            dest="continue_chat",
            help="Continue from the last chat session.",
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

        if args.continue_chat:
            history_dir = config.LOCAL_CHA_CONFIG_HISTORY_DIR
            if not os.path.isdir(history_dir):
                print(colors.yellow("History directory not found. Cannot continue."))
                return

            try:
                json_files = [
                    f
                    for f in os.listdir(history_dir)
                    if f.startswith("cha_hs_") and f.endswith(".json")
                ]
                if not json_files:
                    print(colors.red("No chat history found"))
                    return

                latest_file = max(
                    json_files,
                    key=lambda f: int(re.search(r"cha_hs_(\d+)\.json", f).group(1)),
                )
                history_file_path = os.path.join(history_dir, latest_file)

                with open(history_file_path, "r", encoding="utf-8") as f:
                    history_data = json.load(f)

                chat_history = None
                if isinstance(history_data, dict) and "chat" in history_data:
                    chat_history = history_data["chat"]
                elif isinstance(history_data, list):
                    chat_history = history_data

                if chat_history is None or not isinstance(chat_history, list):
                    raise Exception(
                        f"Invalid history format in {os.path.basename(history_file_path)}"
                    )

                CURRENT_CHAT_HISTORY.clear()
                CURRENT_CHAT_HISTORY.extend(chat_history)
                HISTORY_MODIFIED = False

                from cha import local

                local.print_history_browse_and_select_history_file(CURRENT_CHAT_HISTORY)

            except Exception as e:
                print(colors.red(f"Error loading latest chat history: {e}"))
                return

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
                    HISTORY_MODIFIED = False
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

            try:
                editor.run_editor(
                    client=get_current_chat_client(),
                    model_name=args.model,
                    file_path=args.editor if isinstance(args.editor, str) else None,
                    chat_history=CURRENT_CHAT_HISTORY,
                )
            except editor.InteractiveEditor.ChaAbortException:
                sys.exit(0)
            return

        if args.private:
            save_chat_state = False

        if args.code_dump:
            from cha import codedump

            if args.code_dump is True:
                codedump.code_dump(save_file_to_current_dir=True)
            else:
                arg_str = str(args.code_dump)
                auto_include_all = False
                output_to_stdout = False
                compress_output = False
                specific_includes = None

                options = [opt.strip() for opt in arg_str.split(",") if opt.strip()]

                if "include:" in arg_str:
                    # complex parsing for include:
                    include_parts = arg_str.split("include:", 1)
                    prefix_opts = [
                        p.strip()
                        for p in include_parts[0].split(",")
                        if p.strip() and p != "include:"
                    ]
                    # the rest is include paths and possibly other options
                    include_str = include_parts[1]

                    # find where include paths end and other options begin
                    # this is tricky, so we assume options are single words at the end
                    possible_opts = ["all", "stdout", "compress"]
                    found_opts = []
                    path_part = include_str
                    for opt in possible_opts:
                        if path_part.endswith(f",{opt}"):
                            found_opts.append(opt)
                            path_part = path_part[: -(len(opt) + 1)]

                    specific_includes = [
                        p.strip() for p in path_part.split(",") if p.strip()
                    ]
                    options = prefix_opts + found_opts
                else:
                    # simple parsing
                    options = [opt.strip() for opt in arg_str.split(",") if opt.strip()]

                auto_include_all = "all" in options
                output_to_stdout = "stdout" in options
                compress_output = "compress" in options

                # call codedump to get the content
                content, token_count = codedump.code_dump(
                    output_to_stdout=True,  # always get content back
                    auto_include_all=auto_include_all,
                    specific_includes=specific_includes,
                )

                if content:
                    if compress_output:
                        content = utils.simple_context_compression(
                            content, remove_comments=True
                        )
                        compressed_tokens = utils.count_tokens(content, args.model)
                        if sys.stdout.isatty():
                            print(colors.magenta(f"{compressed_tokens} Total Tokens"))

                    if output_to_stdout:
                        print(content)
                    else:
                        # save to file if not printing to stdout
                        file_name = f"code_dump_{int(time.time())}.txt"
                        with open(file_name, "w", encoding="utf-8") as file:
                            file.write(content)
                        print(colors.green(f"Exported to {file_name}"))
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
                    if not sys.stdout.isatty():
                        pass
                    else:
                        print(colors.blue("User:"), colors.white(recorded_text))
                    chatbot(
                        selected_model, title_print_value, content_string=recorded_text
                    )
                else:
                    if sys.stdout.isatty():
                        print(colors.red("No audio recorded"))
            except Exception as e:
                if sys.stdout.isatty():
                    print(colors.red(f"Recording failed: {e}"))
            return

        if args.platform or config.CHA_CURRENT_PLATFORM_NAME != "openai":
            platform_arg = args.platform
            if not platform_arg and config.CHA_CURRENT_PLATFORM_NAME != "openai":
                platform_arg = config.CHA_CURRENT_PLATFORM_NAME

            try:
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

                if config.CHA_DEFAULT_SHOW_PRINT_TITLE and sys.stdout.isatty():
                    print(
                        colors.magenta(
                            f"Platform switched to {platform_name or BASE_URL_VALUE}"
                        )
                    )

            except Exception as e:
                save_chat_state = False
                raise Exception(f"Failed to switch platform due to {e}")

        if args.select_model:
            new_selected_model = platforms.list_models()
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
                if sys.stdout.isatty():
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
                if sys.stdout.isatty():
                    print(colors.green("Content Type:"), content_mode)
                    print(colors.green("Selected Model:"), args.model)
                    print(colors.green("Text Length:"), len(text), "chars")
                    print(colors.green("Token Count:"), token_count, "tokens")
                else:
                    print(f"{token_count}")
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

        if (
            args.voice_output
            and CURRENT_CHAT_HISTORY
            and CURRENT_CHAT_HISTORY[-1].get("bot")
        ):
            from cha import voice

            loading.start_loading("Speaking", "circles")
            try:
                voice.voice_tool(CURRENT_CHAT_HISTORY[-1]["bot"])
            except Exception as e:
                if sys.stdout.isatty():
                    print(colors.red(f"Voice output failed: {e}"))
            finally:
                loading.stop_loading()

        # handle export logic only if export flag is set and it wasn't an interactive session
        if args.export_parsed_text and input_mode != "interactive":
            if sys.stdout.isatty():
                print()
            # check if there's history to export from (chatbot appends even in non-interactive modes)
            # the first entry is the initial prompt, so we need at least 2 entries for a response.
            if CURRENT_CHAT_HISTORY and len(CURRENT_CHAT_HISTORY) > 1:
                utils.export_file_logic(CURRENT_CHAT_HISTORY[-1]["bot"])
            else:
                if sys.stdout.isatty():
                    print(colors.yellow("No chat response found to export files from"))

    except (KeyboardInterrupt, EOFError):
        if sys.stdout.isatty():
            print()
    except Exception as err:
        if sys.stdout.isatty():
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
            and HISTORY_MODIFIED
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
    if (
        config.CHA_SHOW_VISITED_DIRECTORIES_ON_EXIT
        and VISITED_DIRECTORIES
        and sys.stdout.isatty()
    ):
        formatted_dirs = format_visited_directories(VISITED_DIRECTORIES)
        print(colors.cyan(f"Visited: {formatted_dirs}"))
