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


CURRENT_CHAT_HISTORY = [{"time": time.time(), "user": config.INITIAL_PROMPT, "bot": ""}]


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
            fzf_process = subprocess.run(
                [
                    "fzf",
                    "--reverse",
                    "--height=40%",
                    "--border",
                    "--multi",
                    "--prompt=TAB to multi-select chats to remove, ENTER to confirm: ",
                ],
                input="\n".join(history_items).encode(),
                capture_output=True,
                check=True,
            )
            selected_output = fzf_process.stdout.decode().strip()
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
        f"{config.RUN_ANSWER_FEATURE} - Answer search or '{config.RUN_ANSWER_FEATURE} <query>' for quick search"
    )
    help_options.append(f"{config.TEXT_EDITOR_INPUT_MODE} - Text-editor input mode")
    help_options.append(
        f"{config.SWITCH_MODEL_TEXT} - Switch between models during a session"
    )
    help_options.append(f"{config.USE_CODE_DUMP} - Codedump a directory as context")
    help_options.append(
        f"{config.PICK_AND_RUN_A_SHELL_OPTION} - Pick and run a shell while still being in Cha"
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
            f"{config.LOAD_HISTORY_TRIGGER} - Search and load previous chats"
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
        fzf_process = subprocess.run(
            [
                "fzf",
                "--reverse",
                "--height=40%",
                "--border",
                "--prompt=TAB to multi-select, ENTER to confirm, & Esc to cancel: ",
                "--multi",
                "--header",
                f"Chatting On {config.CHA_CURRENT_PLATFORM_NAME.upper()} With {selected_model}",
            ],
            input="\n".join(help_options).encode(),
            capture_output=True,
            check=True,
        )
        selected_output = fzf_process.stdout.decode().strip()
        if selected_output:
            selected_items = selected_output.split("\n")
            if len(selected_items) == 1 and config.HELP_ALL_ALIAS in selected_items[0]:
                print(
                    colors.yellow(
                        f"Chatting On {config.CHA_CURRENT_PLATFORM_NAME.upper()} With {selected_model}"
                    )
                )
                for help_item in help_options:
                    if config.HELP_ALL_ALIAS not in help_item:
                        print(colors.yellow(help_item))
            else:
                for item in selected_items:
                    if config.HELP_ALL_ALIAS not in item:
                        print(colors.yellow(item))

    except (subprocess.CalledProcessError, subprocess.SubprocessError):
        pass


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
        print(colors.red("No models available to select."))
        return None

    fzf_prompt = f"Select a {config.CHA_CURRENT_PLATFORM_NAME.upper()} model: "
    try:
        fzf_process = subprocess.run(
            ["fzf", "--reverse", "--height=40%", "--border", f"--prompt={fzf_prompt}"],
            input="\n".join(provided_models).encode(),
            capture_output=True,
            check=True,
        )
        selected_model = fzf_process.stdout.decode().strip()
        return selected_model if selected_model else None
    except (subprocess.CalledProcessError, subprocess.SubprocessError):
        return None


def chatbot(selected_model, print_title=True, filepath=None, content_string=None):
    global CURRENT_CHAT_HISTORY

    reasoning_model = utils.is_slow_model(selected_model)

    auto_scrape_detection_mode = False

    # for models (e.g. "o1") that do NOT accept system prompts, skip the system message
    messages = (
        [] if reasoning_model else [{"role": "user", "content": config.INITIAL_PROMPT}]
    )
    multi_line_input = False

    # handle file input or direct content string (non-interactive mode)
    if filepath or content_string:
        if filepath:
            if "/" not in filepath:
                filepath = os.path.join(os.getcwd(), filepath)

            if not os.path.exists(filepath):
                print(colors.red(f"The following file does not exist: {filepath}"))
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

            if message.strip() == config.BACKTRACK_HISTORY_KEY:
                if len(CURRENT_CHAT_HISTORY) <= 1:
                    print(colors.yellow("No chat history to backtrack through."))
                    continue

                selected_indices = backtrack_history(CURRENT_CHAT_HISTORY)
                if selected_indices is not None:
                    original_length = len(CURRENT_CHAT_HISTORY)
                    selected_indices = sorted(selected_indices, reverse=True)

                    for index in selected_indices:
                        if 1 <= index < len(CURRENT_CHAT_HISTORY):
                            CURRENT_CHAT_HISTORY.pop(index)

                    messages = (
                        []
                        if reasoning_model
                        else [{"role": "user", "content": config.INITIAL_PROMPT}]
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

            # handle text-editor input
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
                    # NOTE: this is not user-safe and can cause an error if the user inputs a model name wrong, but it's much faster to do this
                    selected_model = parts[1].strip()
                    print(colors.magenta(f"Switched to model: {selected_model}"))
                    reasoning_model = utils.is_slow_model(selected_model)

                continue

            if message == config.MULTI_LINE_MODE_TEXT:
                multi_line_input = True
                continue

            elif message.replace(" ", "").lower() == config.EXIT_STRING_KEY.lower():
                break

            elif os.path.isdir(
                config.LOCAL_CHA_CONFIG_HISTORY_DIR
            ) and message.strip().lower().startswith(config.LOAD_HISTORY_TRIGGER):
                from cha import local

                hs_output = None
                try:
                    hs_output = local.browse_and_select_history_file()
                    if hs_output:
                        selected_path = hs_output["path"]
                        content = hs_output["content"]
                        chat_msgs = hs_output["chat"]
                except (KeyboardInterrupt, EOFError):
                    print()
                    continue
                except Exception as e:
                    pass
                if hs_output != None:
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
                continue

            if message.startswith(config.PICK_AND_RUN_A_SHELL_OPTION):
                utils.run_a_shell()
                continue

            elif message.replace(" ", "").lower() == config.CLEAR_HISTORY_TEXT.lower():
                messages = (
                    []
                    if reasoning_model
                    else [{"role": "user", "content": config.INITIAL_PROMPT}]
                )
                print(colors.yellow("Chat history cleared."))
                continue

            if multi_line_input:
                # keep appending lines until user types the MULTI_LINE_SEND text
                if message.lower() == config.MULTI_LINE_SEND.lower():
                    multi_line_input = False
                    continue
                message_lines = [message]
                while True:
                    line = utils.safe_input().rstrip("\n")
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

            # print help
            if message.strip().lower() == config.HELP_PRINT_OPTIONS_KEY.lower():
                interactive_help(selected_model)
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
                    if auto_scrape_detection_mode:
                        print(
                            colors.yellow(
                                f"Entered auto url detection & scraping. Type '{config.ENABLE_OR_DISABLE_AUTO_SD}' to exist"
                            )
                        )
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

                            if history_item.get("user"):
                                chat_content += (
                                    f"[{timestamp}] User:\n{history_item['user']}\n\n"
                                )

                            if history_item.get("bot"):
                                chat_content += (
                                    f"[{timestamp}] Bot:\n{history_item['bot']}\n\n"
                                )

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
                        print(colors.yellow("No chat history to export."))
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
                        print(colors.yellow("No history to export."))
                else:
                    if len(CURRENT_CHAT_HISTORY) > 1:
                        last_bot_message = CURRENT_CHAT_HISTORY[-1].get("bot")
                        if last_bot_message:
                            utils.export_file_logic(last_bot_message, force_single)
                        else:
                            print(
                                colors.yellow("Last message has no content to export.")
                            )
                    else:
                        print(colors.yellow("No message to export."))
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
                            {"time": time.time(), "user": "", "bot": message}
                        )
                    except (KeyboardInterrupt, EOFError, SystemExit):
                        pass

                    continue

            # skip if user typed something blank
            if len("".join(str(message)).split()) == 0:
                if auto_scrape_detection_mode == True:
                    auto_scrape_detection_mode = False
                continue

            # add user's message
            messages.append({"role": "user", "content": message})

        # prepare a chat record for local usage
        obj_chat_history = {
            "time": time.time(),
            "user": messages[-1]["content"],
            "bot": "",
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

        except Exception as e:
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
        parser = argparse.ArgumentParser(description="Chat with an OpenAI GPT model.")
        parser.add_argument(
            "-m",
            "--model",
            help="Model to use for chatting",
            default=config.CHA_DEFAULT_MODEL,
        )
        parser.add_argument(
            "-sm",
            "--select_model",
            help="Select one model from OpenAI's supported models",
            action="store_true",
        )
        parser.add_argument(
            "-f",
            "--file",
            help="Filepath to file that will be sent to the model (text only)",
        )
        parser.add_argument(
            "string",
            nargs="*",
            help="Non-interactive mode, feed a string into the model",
        )
        parser.add_argument(
            "-t",
            "--token_count",
            help="Count tokens for the input file or string",
            action="store_true",
        )
        parser.add_argument(
            "-ocr",
            "--ocr",
            help="Given a file path, print the content of that file as text though Cha's main file loading logic",
        )
        parser.add_argument(
            "-p",
            "--platform",
            nargs="?",
            const=True,
            help='Use a different provider, set this like this: "<base_url>|<api_key_env_name>", or use as a flag with "-p" for True',
        )
        parser.add_argument(
            "-d",
            "--code_dump",
            nargs="?",
            const=True,
            help="Do a full code dump into one file in your current directory",
        )
        parser.add_argument(
            "-a",
            "-as",
            "--answer_search",
            help="Run answer search",
            action="store_true",
        )
        parser.add_argument(
            "-e",
            "--export_parsed_text",
            help="Extract code blocks from the final output and save them as files",
            action="store_true",
        )
        parser.add_argument(
            "-ide",
            "--integrated_dev_env",
            help="Input a one-short query using your default terminal text editor (IDE)",
            action="store_true",
        )
        parser.add_argument(
            "-i",
            "--init",
            help="(Optional) Initialize local directory and files in your home directory for configuring Cha",
            action="store_true",
        )
        parser.add_argument(
            "-hs",
            "--history_search",
            help="Search and display a previous chat history without starting a new session",
            action="store_true",
        )
        parser.add_argument(
            "-x",
            "--private",
            help="Enable private mode, no chat history will be saved locally",
            action="store_true",
        )
        parser.add_argument(
            "--editor",
            nargs="?",
            const=True,
            help="Run the interactive editor. Optionally provide a file path.",
        )
        parser.add_argument(
            "-v",
            "--version",
            help="Show version information",
            action="store_true",
        )

        args = parser.parse_args()

        if args.version:
            try:
                from importlib.metadata import version

                print(version("cha"))
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

                hs_output = local.browse_and_select_history_file()
                if hs_output:
                    selected_path = hs_output["path"]
                    chat_msgs = hs_output["chat"]
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

        if (
            args.platform
            or args.platform == True
            or config.CHA_CURRENT_PLATFORM_NAME != "openai"
        ):
            try:
                from cha import platforms

                platform_args = args.platform

                if config.CHA_CURRENT_PLATFORM_NAME != "openai":
                    platform_args = (
                        f"{config.CHA_CURRENT_PLATFORM_NAME}|{config.CHA_DEFAULT_MODEL}"
                    )

                API_KEY_NAME = None
                BASE_URL_VALUE = None
                if (
                    type(platform_args) == str
                    and "|" in platform_args
                    and "http" in platform_args
                ):
                    platform_values = str(platform_args).split("|")
                    API_KEY_NAME = platform_values[1]
                    BASE_URL_VALUE = platform_values[0]
                else:
                    platform_name = None
                    platform_model_name = None
                    if type(platform_args) == str:
                        psplit = platform_args.split("|")
                        platform_name = psplit[0]
                        if len(psplit) == 2:
                            platform_model_name = psplit[1]

                    platform_values = platforms.auto_select_a_platform(
                        platform_key=platform_name,
                        model_name=platform_model_name,
                    )

                    API_KEY_NAME = platform_values["env_name"]
                    BASE_URL_VALUE = platform_values["base_url"]
                    selected_model = platform_values["picked_model"]

                # NOTE: (2-13-2025) this exists to account for cases like this https://ollama.com/blog/openai-compatibility
                API_KEY_VALUE = API_KEY_NAME
                if API_KEY_VALUE in os.environ:
                    API_KEY_VALUE = os.environ.get(API_KEY_NAME)

                set_current_chat_client(API_KEY_VALUE, BASE_URL_VALUE)

                if platform_name == None and type(platform_values) == dict:
                    platform_name = platform_values["platform_name"]
                elif platform_name == None:
                    for platform in config.THIRD_PARTY_PLATFORMS:
                        if platform.lower() in BASE_URL_VALUE.lower().replace(".", ""):
                            platform_name = platform
                            break

                config.CHA_CURRENT_PLATFORM_NAME = platform_name

                if config.CHA_DEFAULT_SHOW_PRINT_TITLE:
                    print(colors.magenta(f"Platform switched to {BASE_URL_VALUE}"))
            except Exception as e:
                save_chat_state = False
                raise Exception(f"Failed to switch platform due to {e}")

        if args.select_model:
            new_selected_model = list_models()
            if new_selected_model:
                selected_model = new_selected_model
            else:
                print(colors.red("No model selected, exiting"))
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
                        "Please provide input text, a filepath, or pipe in content for token counting."
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
                    f"{piped_content}\\n\\n---\\n\\n{' '.join(args.string)}"
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
                print(colors.yellow("No chat response found to export files from."))

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
