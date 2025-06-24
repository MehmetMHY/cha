import traceback
import argparse
import time
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


def title_print(selected_model):
    print(
        colors.yellow(
            utils.rls(
                f"""
                Chatting With {config.CHA_CURRENT_PLATFORM_NAME.upper()} Model: {selected_model}
                - '{config.EXIT_STRING_KEY}' or CTRL-C to exit
                - '{config.CLEAR_HISTORY_TEXT}' to clear chat history
                - '{config.SAVE_CHAT_HISTORY}' to save chat history
                - '{config.LOAD_MESSAGE_CONTENT}' to load a file
                - '{config.HELP_PRINT_OPTIONS_KEY}' to list all options
                - '{config.RUN_ANSWER_FEATURE}' to run answer search
                - '{config.TEXT_EDITOR_INPUT_MODE}' for text-editor input mode
                - '{config.MULTI_LINE_MODE_TEXT}' for multi-line switching (type '{config.MULTI_LINE_SEND}' to send)
                - '{config.SWITCH_MODEL_TEXT}' switch between models during a session
                - '{config.USE_CODE_DUMP}' to codedump a directory as context
                - `{config.EXPORT_FILES_IN_OUTPUT_KEY} [all] [single]` export files from response(s)
                - `{config.PICK_AND_RUN_A_SHELL_OPTION}` pick and run a shell well still being in Cha
                - `{config.ENABLE_OR_DISABLE_AUTO_SD}` enable or disable auto url detection and scraping
                - `{config.USE_FZF_SEARCH}` to use fzf for selection when using `{config.USE_CODE_DUMP}` or `{config.LOAD_MESSAGE_CONTENT}`
                - `{config.RUN_CODER_ALIAS}` to run the coder tool to reduce hallucination
                """
            )
        )
    )

    if os.path.isdir(config.LOCAL_CHA_CONFIG_HISTORY_DIR):
        print(
            colors.cyan(
                f"- '{config.LOAD_HISTORY_TRIGGER} search and load previous chats"
            )
        )

    if len(config.EXTERNAL_TOOLS_EXECUTE) > 0:
        for tool in config.EXTERNAL_TOOLS_EXECUTE:
            alias = tool["alias"]
            about = re.sub(r"[.!?]+$", "", tool["description"].lower())
            print(colors.magenta(f"- '{alias}' {about}"))


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

    print(
        colors.yellow(f"Available {config.CHA_CURRENT_PLATFORM_NAME.upper()} Models:")
    )
    for i in range(len(provided_models)):
        model = provided_models[i]
        print(colors.yellow(f"   {i+1}) {model}"))

    return provided_models


def number_of_urls(text):
    url_pattern = r"https?://(?:www\.)?\S+"
    urls = re.findall(url_pattern, text)
    return len(urls)


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
                print(
                    colors.yellow(
                        f"Entered multi-line input mode. Type '{config.MULTI_LINE_SEND}' to send message"
                    )
                )
                user_input_string = colors.red("[M] ") + colors.blue("User: ")

            if auto_scrape_detection_mode:
                user_input_string = colors.yellow("[S] ") + colors.blue("User: ")

            message = utils.safe_input(user_input_string).rstrip("\n")

            if message.startswith((config.USE_FZF_SEARCH)):
                print(
                    colors.red(
                        f"Fzf search can only be used in `{config.USE_CODE_DUMP}` or `{config.LOAD_MESSAGE_CONTENT}`"
                    )
                )
                continue

            if message.strip().startswith(config.RUN_CODER_ALIAS):
                coder_message = None
                if len(message.split(" ")) > 1:
                    coder_message = message.replace(config.RUN_CODER_ALIAS, "").strip()

                try:
                    from cha import coder

                    code_messages = coder.call_coder(
                        client=get_current_chat_client(),
                        initial_prompt=coder_message,
                        model_name=selected_model,
                        max_retries=3,
                    )

                    messages.extend(code_messages)
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
                    provided_models = list_models()

                    selection = utils.safe_input(
                        colors.blue(f"Select a model (1-{len(provided_models)}): ")
                    )
                    if selection.isdigit():
                        idx = int(selection) - 1
                        if 0 <= idx < len(provided_models):
                            selected_model = provided_models[idx]
                            print(
                                colors.magenta(f"Switched to model: {selected_model}")
                            )
                            reasoning_model = utils.is_slow_model(selected_model)
                        else:
                            print(colors.red("Invalid model number."))
                    else:
                        print(colors.red("Invalid input."))

                else:
                    # NOTE: this is not user-safe and can cause an error if the user inputs a model name wrong, but it's much faster to do this
                    selected_model = parts[1].strip()
                    print(colors.magenta(f"Switched to model: {selected_model}"))
                    reasoning_model = utils.is_slow_model(selected_model)

                continue

            if message == config.MULTI_LINE_MODE_TEXT:
                multi_line_input = True
                continue

            elif message.replace(" ", "") == config.EXIT_STRING_KEY.lower():
                break

            elif os.path.isdir(
                config.LOCAL_CHA_CONFIG_HISTORY_DIR
            ) and message.strip().lower().startswith(config.LOAD_HISTORY_TRIGGER):
                from cha import local

                hs_output = None
                try:
                    hs_output = local.browse_and_select_history_file()
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
                    messages.append(
                        {
                            "role": "user",
                            "content": utils.rls(
                                f"""
                                Load the following chat history into the current chat:
                                {str(content)}
                                """
                            ),
                        }
                    )
                continue

            if message.startswith(config.PICK_AND_RUN_A_SHELL_OPTION):
                utils.run_a_shell()
                continue

            elif message.replace(" ", "") == config.CLEAR_HISTORY_TEXT:
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
            for tool_data in config.EXTERNAL_TOOLS_EXECUTE:
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

            if message.strip().startswith(config.ENABLE_OR_DISABLE_AUTO_SD):
                if auto_scrape_detection_mode == False and number_of_urls(message) > 0:
                    loading.start_loading("Scraping URL(s)", "basic")
                    from cha import scraper

                    try:
                        message = scraper.scraped_prompt(message)
                    finally:
                        loading.stop_loading()
                else:
                    auto_scrape_detection_mode = not auto_scrape_detection_mode
                    if auto_scrape_detection_mode:
                        print(
                            colors.yellow(
                                f"Entered auto url detection & scraping. Type '{config.ENABLE_OR_DISABLE_AUTO_SD}' to exist"
                            )
                        )
                    continue

            # save chat history to a JSON file
            if message == config.SAVE_CHAT_HISTORY:
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

            # print help
            if message == config.HELP_PRINT_OPTIONS_KEY:
                title_print(selected_model)
                continue

            # prompt user to load a file
            if message == config.LOAD_MESSAGE_CONTENT:
                from cha import traverse

                message = traverse.msg_content_load(get_current_chat_client())
                if message is None:
                    continue

            if message.startswith(config.USE_CODE_DUMP):
                try:
                    from cha import codedump

                    dir_path = message.replace(config.USE_CODE_DUMP, "").replace(
                        " ", ""
                    )
                    if "/" not in str(dir_path):
                        dir_path = None
                    message = codedump.code_dump(dir_full_path=dir_path)
                    if message == None:
                        continue
                except (KeyboardInterrupt, EOFError):
                    print()
                    continue

            # check for URLs -> scraping
            if auto_scrape_detection_mode:
                if number_of_urls(message) > 0:
                    loading.start_loading("Scraping URLs", "star")
                    from cha import scraper

                    try:
                        message = scraper.scraped_prompt(message)
                    finally:
                        loading.stop_loading()

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
            "-c",
            "--coder",
            nargs="?",
            const=True,
            help="Run the coder tool to reduce hallucination",
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

        args = parser.parse_args()

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

        if args.private:
            save_chat_state = False

        if args.code_dump == True:
            from cha import codedump

            codedump.code_dump(None, True)
            return

        if args.ocr != None:
            content = None

            if number_of_urls(str(args.ocr)) > 0:
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
            provided_models = list_models()

            selection = utils.safe_input(
                colors.blue(f"Select a model (1-{len(provided_models)}): ")
            )
            selected_a_model = False
            if selection.isdigit():
                selection = int(selection) - 1
                if 0 <= selection < len(provided_models):
                    selected_model = provided_models[selection]
                    selected_a_model = True
            if selected_a_model == False:
                print(colors.red("Invalid number selected!"))
                return

        if args.coder:
            try:
                from cha import coder

                initial_prompt = args.coder if isinstance(args.coder, str) else None
                conversation_history = coder.call_coder(
                    client=get_current_chat_client(),
                    initial_prompt=initial_prompt,
                    model_name=selected_model,
                    max_retries=3,
                )
            except (KeyboardInterrupt, EOFError, SystemExit):
                return None
            except Exception as e:
                save_chat_state = False
                raise Exception(f"Coder feature failed: {e}")

            save_chat_state = False
            if conversation_history is None:
                raise Exception("Coder feature exited with None")

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
                "id": file_id,
                "version": version_id,
                "date": {
                    "epoch": {"seconds": epoch_time_seconds},
                    "utc": utc_time_stamp,
                },
                "args": {},
                "config": utils.get_json_serializable_globals(config),
                "chat": CURRENT_CHAT_HISTORY,
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
