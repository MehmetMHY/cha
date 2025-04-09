import sys

# NOTE: account for early keyboard exist
try:
    import argparse
    import time
    import json
    import os

    from cha import (
        scraper,
        colors,
        utils,
        config,
        loading,
        platforms,
        codedump,
        answer,
        traverse,
    )

    from openai import OpenAI
except (KeyboardInterrupt, EOFError):
    sys.exit(1)

utils.check_env_variable("OPENAI_API_KEY", config.OPENAI_DOCS_LINK)

openai_client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
)

client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
)

CURRENT_CHAT_HISTORY = [{"time": time.time(), "user": config.INITIAL_PROMPT, "bot": ""}]


def title_print(selected_model):
    print(
        colors.yellow(
            utils.rls(
                f"""
                Chatting With OpenAI's '{selected_model}' Model
                - '{config.EXIT_STRING_KEY}' or CTRL-C to exit
                - '{config.CLEAR_HISTORY_TEXT}' to clear chat history
                - '{config.SAVE_CHAT_HISTORY}' to save chat history
                - '{config.LOAD_MESSAGE_CONTENT}' to load a file
                - '{config.HELP_PRINT_OPTIONS_KEY}' to list all options
                - '{config.RUN_ANSWER_FEATURE}' to run answer search
                - '{config.TEXT_EDITOR_INPUT_MODE}' for text-editor input mode
                - '{config.MULTI_LINE_MODE_TEXT}' for single/multi-line switching
                - '{config.MULTI_LINE_SEND}' to end in multi-line mode
                - '{config.SWITCH_MODEL_TEXT}' switch between models during a session
                - '{config.USE_CODE_DUMP}' to codedump a directory as context
                - `{config.QUICK_WEB_SEARCH_ANSWER}` answer prompt with a quick web search
                - `{config.EXPORT_FILES_IN_OUTPUT_KEY}` export all files generated my the model
                - `{config.PICK_AND_RUN_A_SHELL_OPTION}` pick and run a shell well still being in Cha
                """
            )
        )
    )


def list_models():
    try:
        response = openai_client.models.list()
        if not response.data:
            raise ValueError("No models available")

        return [
            (model.id, model.created)
            for model in response.data
            if any(substr in model.id for substr in config.OPENAI_MODELS_TO_KEEP)
            and not any(substr in model.id for substr in config.OPENAI_MODELS_TO_IGNORE)
        ]
    except Exception as e:
        print(colors.red(f"Error fetching models: {e}"))
        sys.exit(1)


def cleanly_print_models(openai_models):
    print(colors.yellow("Available OpenAI Models:"))
    openai_models = sorted(openai_models, key=lambda x: x[1])
    max_index_length = len(str(len(openai_models)))
    max_model_id_length = max(len(model_id) for model_id, _ in openai_models)
    for index, (model_id, created) in enumerate(openai_models, start=1):
        padded_index = str(index).rjust(max_index_length)
        padded_model_id = model_id.ljust(max_model_id_length)
        print(
            colors.yellow(
                f"   {padded_index}) {padded_model_id}   {utils.simple_date(created)}"
            )
        )
    return openai_models


def chatbot(selected_model, print_title=True, filepath=None, content_string=None):
    global client
    global CURRENT_CHAT_HISTORY

    reasoning_model = utils.is_slow_model(selected_model)

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
                    client=openai_client,
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

            message = utils.safe_input(user_input_string).rstrip("\n")

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
                    openai_models = cleanly_print_models(openai_models=list_models())

                    selection = utils.safe_input(
                        colors.blue(f"Select a model (1-{len(openai_models)}): ")
                    )
                    if selection.isdigit():
                        idx = int(selection) - 1
                        if 0 <= idx < len(openai_models):
                            selected_model = openai_models[idx][0]
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
                message_lines = [message]
                while True:
                    line = utils.safe_input().rstrip("\n")
                    if line.lower() == config.MULTI_LINE_SEND.lower():
                        break
                    message_lines.append(line)
                message = "\n".join(message_lines)
                multi_line_input = False

            # save chat history to a JSON file
            if message == config.SAVE_CHAT_HISTORY:
                cha_filepath = f"cha_{int(time.time())}.json"
                utils.write_json(cha_filepath, CURRENT_CHAT_HISTORY)
                print(colors.red(f"Saved current chat history to {cha_filepath}"))
                continue

            if message.strip() == config.EXPORT_FILES_IN_OUTPUT_KEY:
                utils.export_file_logic(CURRENT_CHAT_HISTORY[-1]["bot"])
                continue

            # print help
            if message == config.HELP_PRINT_OPTIONS_KEY:
                title_print(selected_model)
                continue

            # prompt user to load a file
            if message == config.LOAD_MESSAGE_CONTENT:
                message = traverse.msg_content_load(openai_client)
                if message is None:
                    continue

            if message.startswith(config.USE_CODE_DUMP):
                try:
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
            detected_urls = len(scraper.extract_urls(message))
            if detected_urls > 0:
                du_print = f"{detected_urls} URL{'s' if detected_urls > 1 else ''}"
                prompt = f"{du_print} detected, continue web scraping (y/n)? "
                sys.stdout.write(colors.red(prompt))
                sys.stdout.flush()
                du_user = utils.safe_input().strip()
                sys.stdout.write(config.MOVE_CURSOR_ONE_LINE)
                sys.stdout.write(config.CLEAR_LINE)
                sys.stdout.flush()

                if du_user.lower() in ["y", "yes"]:
                    loading.start_loading("Scraping URLs", "star")
                    try:
                        message = scraper.scraped_prompt(message)
                    finally:
                        loading.stop_loading()

            if message.startswith(config.QUICK_WEB_SEARCH_ANSWER):
                if len(message) <= len(str(config.QUICK_WEB_SEARCH_ANSWER)) * 2:
                    print(
                        colors.red(
                            f"Usage: {config.QUICK_WEB_SEARCH_ANSWER} <question>"
                        )
                    )
                    continue
                message = message.replace(config.QUICK_WEB_SEARCH_ANSWER, "").strip()
                new_message = answer.quick_search(user_input=message)
                if new_message == None:
                    print(colors.red(f"Failed to do a quick web search"))
                else:
                    message = new_message

            if message.startswith(config.PICK_AND_RUN_A_SHELL_OPTION):
                utils.run_a_shell()
                continue

            # check for an answer-search command
            if message.startswith(config.RUN_ANSWER_FEATURE):
                user_input_mode = True
                answer_prompt = None
                if len(message) > len(config.RUN_ANSWER_FEATURE):
                    answer_prompt_draft = message[
                        len(config.RUN_ANSWER_FEATURE) :
                    ].strip()
                    if len(answer_prompt_draft) > 10:
                        user_input_mode = False
                        answer_prompt = answer_prompt_draft

                message = utils.run_answer_search(
                    client=openai_client,
                    prompt=answer_prompt,
                    user_input_mode=user_input_mode,
                )

                if message is not None:
                    messages.append({"role": "user", "content": message})

                continue

            # skip if user typed something blank
            if len("".join(str(message)).split()) == 0:
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
                response = client.chat.completions.create(
                    model=selected_model, messages=messages
                )
                loading.stop_loading()
                full_response = response.choices[0].message.content
                print(colors.green(full_response))
                obj_chat_history["bot"] = full_response

            else:
                response = client.chat.completions.create(
                    model=selected_model, messages=messages, stream=True
                )
                full_response = ""
                try:
                    for chunk in response:
                        try:
                            chunk_message = chunk.choices[0].delta.content
                        except:
                            break
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
    global client

    try:
        parser = argparse.ArgumentParser(description="Chat with an OpenAI GPT model.")
        parser.add_argument(
            "-pt",
            "--print_title",
            help="Print initial title during interactive mode",
            action="store_true",
        )
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

        args = parser.parse_args()

        if args.code_dump == True:
            codedump.code_dump(None, True)
            return

        if args.ocr != None:
            content = None

            detected_urls = scraper.extract_urls(str(args.ocr))
            if len(detected_urls) > 0:
                for i in range(len(detected_urls)):
                    detected_urls[i] = str(detected_urls[i]).replace("\\", "")
                content = scraper.get_all_htmls(detected_urls)
            else:
                content = utils.act_as_ocr(
                    client=openai_client, filepath=str(args.ocr), prompt=None
                )

            if content == None:
                print(colors.red(f"Failed to load file due to an error"))
            elif type(content) == dict:
                print(json.dumps(content, indent=4))
            else:
                print(content)
            return

        if args.answer_search == True:
            output = utils.run_answer_search(
                client=openai_client, prompt=None, user_input_mode=True
            )
            sys.exit(1 if output is None else 0)

        title_print_value = args.print_title
        selected_model = args.model

        if args.platform or args.platform == True:
            try:
                print(colors.red("WARNING: Switching platforms is experimental!"))
                API_KEY_NAME = None
                BASE_URL_VALUE = None
                if (
                    type(args.platform) == str
                    and "|" in args.platform
                    and "http" in args.platform
                ):
                    platform_values = str(args.platform).split("|")
                    API_KEY_NAME = platform_values[1]
                    BASE_URL_VALUE = platform_values[0]
                else:
                    platform_name = None
                    platform_model_name = None
                    if type(args.platform) == str:
                        psplit = args.platform.split("|")
                        platform_name = psplit[0]
                        if len(psplit) == 2:
                            platform_model_name = psplit[1]

                    platform_values = platforms.auto_select_a_platform(
                        client=openai_client,
                        platform_key=platform_name,
                        model_name=platform_model_name,
                    )

                    API_KEY_NAME = platform_values["env_name"]
                    BASE_URL_VALUE = platform_values["base_url"]
                    selected_model = platform_values["picked_model"]

                if platform_values.get("type") == "package_call":
                    return

                # NOTE: (2-13-2025) this exists to account for cases like this: https://ollama.com/blog/openai-compatibility
                API_KEY_VALUE = API_KEY_NAME
                if API_KEY_VALUE in os.environ:
                    API_KEY_VALUE = os.environ.get(API_KEY_NAME)

                client = OpenAI(
                    api_key=API_KEY_VALUE,
                    base_url=BASE_URL_VALUE,
                )

                print(colors.magenta(f"Platform switched to {BASE_URL_VALUE}"))
            except Exception as e:
                print(colors.red(f"Failed to switch platform due to {e}"))
                return

        if args.token_count:
            text, content_mode = None, None

            if args.file:
                content_mode = "FILE"
                text = utils.load_most_files(args.file, openai_client)
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
            except Exception as e:
                print(colors.red(f"Error counting tokens: {e}"))
            return

        if args.select_model:
            openai_models = cleanly_print_models(openai_models=list_models())

            selection = utils.safe_input(
                colors.blue(f"Select a model (1-{len(openai_models)}): ")
            )
            if selection.isdigit():
                selection = int(selection) - 1
                if 0 <= selection < len(openai_models):
                    selected_model = openai_models[selection][0]
            else:
                print(colors.red("Invalid number selected. Exiting."))
                return

        if args.file:
            chatbot(selected_model, title_print_value, filepath=args.file)
        elif args.string:
            chatbot(
                selected_model, title_print_value, content_string=" ".join(args.string)
            )
        elif args.integrated_dev_env:
            editor_content = utils.check_terminal_editors_and_edit()
            if editor_content is None:
                print(colors.red(f"No text editor available or editing cancelled"))
                sys.exit(1)
            chatbot(selected_model, title_print_value, content_string=editor_content)
        else:
            chatbot(selected_model=selected_model, print_title=title_print_value)

        if args.export_parsed_text:
            print()
            utils.export_file_logic(CURRENT_CHAT_HISTORY[-1]["bot"])

    except (KeyboardInterrupt, EOFError):
        print()
    except Exception as err:
        if str(err):
            # NOTE: a newline is needed to prevent text overlap during streaming cancellation
            print(colors.red(f"\nAn error occurred: {err}"))
        else:
            print(colors.red("Exited unexpectedly"))
        sys.exit(1)
