import sys

try:
    import argparse
    import time
    import os
    from openai import OpenAI
    from cha import scraper, colors, image, utils, config, loading
except (KeyboardInterrupt, EOFError):
    sys.exit(1)

utils.check_env_variable("OPENAI_API_KEY", config.OPENAI_DOCS_LINK)

client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
)

CURRENT_CHAT_HISTORY = [{"time": time.time(), "user": config.INITIAL_PROMPT, "bot": ""}]


def title_print(selected_model):
    print(
        colors.yellow(
            "\n".join(
                line.strip()
                for line in f"""
Chatting With OpenAI's '{selected_model}' Model
- '{config.EXIT_STRING_KEY}' or CTRL-C to exit
- '{config.CLEAR_HISTORY_TEXT}' to clear chat history
- '{config.IMG_GEN_MODE}' for image generation
- '{config.SAVE_CHAT_HISTORY}' to save chat history
- '{config.LOAD_MESSAGE_CONTENT}' to load a file
- '{config.HELP_PRINT_OPTIONS_KEY}' to list all options
- '{config.RUN_ANSWER_FEATURE}' to run answer search
- '{config.TEXT_EDITOR_INPUT_MODE}' for text-editor input mode
- '{config.MULTI_LINE_MODE_TEXT}' for single/multi-line switching
- '{config.MULTI_LINE_SEND}' to end in multi-line mode
                """.strip().splitlines()
            )
        )
    )


def list_models():
    try:
        response = client.models.list()
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


def chatbot(selected_model, print_title=True, filepath=None, content_string=None):
    global client

    is_o1 = utils.is_o_model(selected_model)

    # NOTE: for o-models that don't accept system prompts
    messages = [] if is_o1 else [{"role": "system", "content": config.INITIAL_PROMPT}]
    multi_line_input = False

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
                loading.start_loading("Loading Image", "rectangles")
                content = utils.load_most_files(
                    client=client,
                    file_path=filepath,
                    model_name=config.CHA_DEFAULT_IMAGE_MODEL,
                )
            except:
                raise Exception(f"failed to load file {filepath}")
            finally:
                loading.stop_loading()
                pass
        else:
            content = content_string

        messages.append({"role": "user", "content": content})
        single_response = True
    else:
        if print_title:
            title_print(selected_model)
        single_response = False

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

            if message == config.TEXT_EDITOR_INPUT_MODE:
                editor_content = utils.check_terminal_editors_and_edit()
                if editor_content == None:
                    print(colors.red(f"No text editor available or editing cancelled"))
                    continue
                message = editor_content
                if len(message) == 0:
                    continue
                for line in message.rstrip("\n").split("\n"):
                    print(colors.blue(">"), line)

            if message == config.MULTI_LINE_MODE_TEXT:
                multi_line_input = True
                continue
            elif message.replace(" ", "") == config.IMG_GEN_MODE:
                image.gen_image(client=client)
                continue
            elif message.replace(" ", "") == config.EXIT_STRING_KEY.lower():
                break
            elif message.replace(" ", "") == config.CLEAR_HISTORY_TEXT:
                messages = (
                    []
                    if is_o1
                    else [{"role": "system", "content": config.INITIAL_PROMPT}]
                )
                print(colors.yellow("Chat history cleared."))
                continue

            if multi_line_input:
                message_lines = [message]
                while True:
                    line = utils.safe_input().rstrip("\n")
                    if line.lower() == config.MULTI_LINE_SEND.lower():
                        break
                    message_lines.append(line)
                message = "\n".join(message_lines)
                multi_line_input = False

            if message == config.SAVE_CHAT_HISTORY:
                cha_filepath = f"cha_{int(time.time())}.json"
                utils.write_json(cha_filepath, CURRENT_CHAT_HISTORY)
                print(colors.red(f"Saved current saved history to {cha_filepath}"))
                continue

            if message == config.HELP_PRINT_OPTIONS_KEY:
                title_print(selected_model)
                continue

            if message == config.LOAD_MESSAGE_CONTENT:
                try:
                    message = utils.msg_content_load(client)
                except:
                    message = None
                if message is None:
                    print()
                    continue

            detected_urls = len(scraper.extract_urls(message))
            if detected_urls > 0:
                # NOTE: determine whether scraping should happen, and then clear the input text message afterwards
                du_print = f"{detected_urls} URL{'s' if detected_urls > 1 else ''}"
                prompt = f"{du_print} detected, continue web scraping (y/n)? "
                sys.stdout.write(colors.red(prompt))
                sys.stdout.flush()
                du_user = utils.safe_input().strip()
                sys.stdout.write(config.MOVE_CURSOR_ONE_LINE)
                sys.stdout.write(config.CLEAR_LINE)
                sys.stdout.flush()

                if du_user.lower() == "y" or du_user.lower() == "yes":
                    loading.start_loading("Scraping URLs", "star")

                    try:
                        message = scraper.scraped_prompt(message)
                    finally:
                        loading.stop_loading()

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
                    client=client, prompt=answer_prompt, user_input_mode=user_input_mode
                )

                if message != None:
                    messages.append({"role": "user", "content": message})

                continue

            if len("".join(str(message)).split()) == 0:
                continue

            messages.append({"role": "user", "content": message})

        obj_chat_history = {
            "time": time.time(),
            "user": messages[-1]["content"],
            "bot": "",
        }

        try:
            if is_o1:
                loading.start_loading("Thinking", "braille")

                # NOTE: o1 models don't support streaming
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
                # NOTE: only print the newline for completed streamed responses
                if not is_o1 and full_response.endswith("\n") == False:
                    sys.stdout.write("\n")
                    sys.stdout.flush()

        except Exception as e:
            print(colors.red(f"\nError during chat: {e}"))
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
            "-a",
            "-as",
            "--answer_search",
            help="Run answer search",
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
            "-i",
            "--image",
            nargs="?",
            const=True,
            default=False,
            help="Generate image (flag only) or print the metadata for generated images (provide filepath)",
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
            default=None,
            help='Use a different provider, set this like this: "<base_url>|<api_key_env_name>"',
        )

        args = parser.parse_args()

        if args.ocr != None:
            try:
                filepath = str(args.ocr)
                if "/" not in filepath:
                    filepath = "./" + filepath
                content = utils.load_most_files(file_path=filepath, client=client)
                print(content)
            except Exception as e:
                print(colors.red(f"Failed to load file {filepath} due to {e}"))
            return

        if args.image:
            if args.image == True:
                status = image.gen_image(client=client)
            else:
                status = image.display_metadata(str(args.image))
            sys.exit(1 if status is None else 0)

        if args.answer_search == True:
            output = utils.run_answer_search(
                client=client, prompt=None, user_input_mode=True
            )
            sys.exit(1 if output is None else 0)

        title_print_value = args.print_title
        selected_model = args.model

        if args.platform:
            try:
                platform_values = str(args.platform).split("|")
                client = OpenAI(
                    api_key=os.environ.get(platform_values[1]),
                    base_url=platform_values[0],
                )
                print(
                    colors.red(
                        f"Warning! The platform switched to {platform_values[0]}"
                    )
                )
            except Exception as e:
                print(colors.red(f"Failed to switch platform due to {e}"))
                return

        if args.token_count:
            text, content_mode = None, None

            if args.file:
                content_mode = "FILE"
                text = utils.load_most_files(args.file, client)
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
            openai_models = list_models()
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

        if args.string and args.file:
            print(
                colors.red("You can't use the string and file option at the same time!")
            )
        elif args.file:
            chatbot(selected_model, title_print_value, filepath=args.file)
        elif args.string:
            chatbot(
                selected_model, title_print_value, content_string=" ".join(args.string)
            )
        else:
            chatbot(selected_model=selected_model, print_title=title_print_value)

    except (KeyboardInterrupt, EOFError):
        print()
    except Exception as err:
        if str(err):
            # NOTE: a newline is needed to prevent text overlap during streaming cancellation
            print(colors.red(f"\nAn error occurred: {err}"))
        else:
            print(colors.red("Exited unexpectedly"))
        sys.exit(1)
