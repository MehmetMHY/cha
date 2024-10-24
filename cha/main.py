import sys

# NOTE: this exists to prevent a ugly print from showing if some cancels quickly
try:
    import argparse
    import json
    import time
    import os

    from openai import OpenAI
    from cha import scraper, colors, image, utils, config
except (KeyboardInterrupt, EOFError):
    sys.exit(1)

utils.check_env_variable("OPENAI_API_KEY", config.OPENAI_DOCS_LINK)

# global, in memory, variables
CURRENT_CHAT_HISTORY = [{"time": time.time(), "user": config.INITIAL_PROMPT, "bot": ""}]

client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
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


def title_print(selected_model):
    print(
        colors.yellow(
            f"""Chatting With OpenAI's '{selected_model}' Model
 - '{config.EXIT_STRING_KEY}' or CTRL-C to exit
 - '{config.MULI_LINE_MODE_TEXT}' for single/multi-line mode
 - '{config.MULTI_LINE_SEND}' to end in multi-line mode
 - '{config.CLEAR_HISTORY_TEXT}' to clear chat history
 - '{config.IMG_GEN_MODE}' for image generation
 - '{config.SAVE_CHAT_HISTORY}' to save chat history
 - '{config.LOAD_MESSAGE_CONTENT}' to load a file into your prompt
 - '{config.HELP_PRINT_OPTIONS_KEY}' list all options"""
        ).strip()
    )


def msg_content_load():
    files = [f for f in os.listdir() if os.path.isfile(f)]

    if len(files) == 0:
        print(colors.red(f"No files found in the current directory"), end="")
        return None

    print(colors.yellow(f"Current Directory:"), os.getcwd())
    print(colors.yellow("File(s):"))
    for i in range(len(files)):
        print(f"   {i+1}) {files[i]}")

    while True:
        try:
            file_pick = input(colors.yellow(f"File ID (1-{len(files)}): "))
            file_path = files[int(file_pick) - 1]
            break
        except KeyboardInterrupt:
            return None
        except EOFError:
            return None
        except:
            pass

    with open(file_path, "r") as file:
        content = file.read()

    prompt = input(colors.yellow("Additional Prompt: "))

    output = content
    if len(prompt) > 0:
        output = f"""
PROMPT: {prompt}
CONTENT:
``````````
{content}
``````````
"""

    return output


def chatbot(selected_model, print_title=True, filepath=None, content_string=None):
    messages = [{"role": "system", "content": config.INITIAL_PROMPT}]
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
                    f"Feeding the following file content to {selected_model}:"
                )
            )
            print(colors.yellow(f"   > {filepath}"))
            print()

            content = "\n".join(utils.read_file(filepath))
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

            if message == config.MULI_LINE_MODE_TEXT:
                multi_line_input = True
                continue
            elif message.replace(" ", "") == config.IMG_GEN_MODE:
                image.gen_image(client=client)
                continue
            elif message.replace(" ", "") == config.EXIT_STRING_KEY.lower():
                break
            elif message.replace(" ", "") == config.CLEAR_HISTORY_TEXT:
                messages = [{"role": "system", "content": config.INITIAL_PROMPT}]
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
                message = msg_content_load()
                if message is None:
                    print()
                    continue

            detected_urls = len(scraper.extract_urls(message))
            if detected_urls > 0:
                du_print = f"{detected_urls} URL{'s' if detected_urls > 1 else ''}"
                du_user = utils.safe_input(
                    colors.red(f"{du_print} detected, continue web scraping (y/n)? ")
                )
                if du_user.lower() == "y" or du_user.lower() == "yes":
                    message = scraper.scraped_prompt(message)

            if len(message) == 0:
                raise KeyboardInterrupt

            messages.append({"role": "user", "content": message})

        obj_chat_history = {
            "time": time.time(),
            "user": messages[-1]["content"],
            "bot": "",
        }

        try:
            response = client.chat.completions.create(
                model=selected_model, messages=messages, stream=True
            )

            full_response = ""
            for chunk in response:
                chunk_message = chunk.choices[0].delta.content
                if chunk_message:
                    sys.stdout.write(colors.green(chunk_message))
                    full_response += chunk_message
                    obj_chat_history["bot"] += chunk_message
                    sys.stdout.flush()

            if full_response:
                messages.append({"role": "assistant", "content": full_response})
                sys.stdout.write("\n")
                sys.stdout.flush()
        except Exception as e:
            print(colors.red(f"Error during chat: {e}"))
            break

        CURRENT_CHAT_HISTORY.append(obj_chat_history)

        if single_response:
            break


def cli():
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
            "-igmd", "--ig_metadata", help="Print the meta data for generated images"
        )
        parser.add_argument(
            "-t",
            "--token_count",
            help="Count tokens for the input file or string",
            action="store_true",
        )

        args = parser.parse_args()

        if args.ig_metadata:
            filepath = str(args.ig_metadata)
            status = image.display_metadata(filepath)
            sys.exit(1 if status is None else 0)

        title_print_value = args.print_title
        selected_model = args.model

        if args.token_count:
            text, content_mode = None, None

            if args.file:
                content_mode = "FILE"
                with open(args.file, "r", encoding="utf-8") as file:
                    text = file.read()
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
                print(colors.green("Text Length:"), len(text))
                print(colors.green("Token Count:"), token_count)
            except Exception as e:
                print(colors.red(f"Error counting tokens: {e}"))
            return

        if args.select_model:
            openai_models = list_models()
            print(colors.yellow("Available OpenAI Models:"))
            max_length = max(len(model_id) for model_id, _ in openai_models)
            openai_models = sorted(openai_models, key=lambda x: x[1])
            for model_id, created in openai_models:
                formatted_model_id = model_id.ljust(max_length)
                print(
                    colors.yellow(
                        f"   > {formatted_model_id}   {utils.simple_date(created)}"
                    )
                )
            selected_model = utils.safe_input(
                colors.blue("Which model do you want to use? ")
            )
            if selected_model not in [model[0] for model in openai_models]:
                print(colors.red("Invalid model selected. Exiting."))
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
            chatbot(selected_model, title_print_value)

    except (KeyboardInterrupt, EOFError):
        print()
    except Exception as err:
        if str(err):
            print(colors.red(f"An error occurred: {err}"))
        else:
            print(colors.red("Exited unexpectedly"))
        sys.exit(1)
