import argparse
import datetime
import copy
import json
import time
import sys
import os

# NOTE: make sure environment variable is defined before doing anything
if "OPENAI_API_KEY" not in os.environ:
    print("Can't proceed because an OPENAI_API_KEY env variable is not defined!")
    sys.exit(1)

# 3rd party packages
from openai import OpenAI
from cha import scraper, youtube, colors, image, config


# global, in memory, variables
CURRENT_CHAT_HISTORY = [{"time": time.time(), "user": config.INITIAL_PROMPT, "bot": ""}]

client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
)


def simple_date(epoch_time):
    date_time = datetime.datetime.fromtimestamp(epoch_time)
    formatted_date = date_time.strftime("%B %d, %Y")
    return formatted_date


def list_models():
    try:
        response = client.models.list()
        if not response.data:
            raise ValueError("No models available")

        openai_models = [
            (model.id, model.created)
            for model in response.data
            if "gpt" in model.id and "instruct" not in model.id
        ]

        return openai_models
    except Exception as e:
        print(colors.red(f"Error fetching models: {e}"))
        sys.exit(1)


def title_print(selected_model):
    # last updated: 9-16-2024
    print(
        colors.yellow(
            f"""Chatting With OpenAI's '{selected_model}' Model
 - '{config.EXIT_STRING_KEY}' or CTRL-C to exit
 - '{config.MULI_LINE_MODE_TEXT}' for single/multi-line mode
 - '{config.MULTI_LINE_SEND}' to end in multi-line mode
 - '{config.CLEAR_HISTORY_TEXT}' to clear chat history
 - '{config.IMG_GEN_MODE}' for image generation
 - '{config.SAVE_CHAT_HISTORY}' to save chat history"""
        ).strip()
    )


def chatbot(selected_model, print_title=True):
    messages = [{"role": "system", "content": config.INITIAL_PROMPT}]
    multi_line_input = False
    first_loop = True

    # print the initial title
    if print_title == True:
        title_print(selected_model)

    line_mode = False
    last_line = ""
    while True:
        if first_loop == False:
            print()

        if last_line.endswith("\n") == False:
            print()

        user_input_string = colors.blue(f"User: ")
        if line_mode:
            print(
                colors.yellow(
                    f"Entered multi-line input mode. Type '{config.MULTI_LINE_SEND}' to send message"
                )
            )
            user_input_string = colors.red("[M]") + " " + colors.blue(f"User: ")
        print(colors.blue(user_input_string), end="", flush=True)

        first_loop = False

        if not multi_line_input:
            message = sys.stdin.readline().rstrip("\n")

            if message == config.MULI_LINE_MODE_TEXT:
                multi_line_input = True
                line_mode = True
                last_line = "\n"
                continue
            elif message.replace(" ", "") == config.IMG_GEN_MODE:
                print("\n")
                image.gen_image()
                continue
            elif message.replace(" ", "") == config.EXIT_STRING_KEY.lower():
                break
            elif message.replace(" ", "") == config.CLEAR_HISTORY_TEXT:
                messages = [{"role": "system", "content": config.INITIAL_PROMPT}]
                print(colors.yellow("\n\nChat history cleared.\n"))
                first_loop = True
                continue

        if multi_line_input:
            message_lines = []
            while True:
                line = sys.stdin.readline().rstrip("\n")
                if line.lower() == config.MULTI_LINE_SEND.lower():
                    break
                elif (
                    line.replace(" ", "").replace("\n", "") == config.CLEAR_HISTORY_TEXT
                ):
                    messages = [{"role": "system", "content": config.INITIAL_PROMPT}]
                    print(colors.yellow("\n\nChat history cleared.\n"))
                    first_loop = True
                    break
                message_lines.append(line)
            message = "\n".join(message_lines)
            line_mode = False
            multi_line_input = False

        # NOTE: this is annoying, but we have to account for this :(
        print()

        if message == config.SAVE_CHAT_HISTORY:
            cha_filepath = f"cha_{int(time.time())}.txt"
            youtube.write_json(cha_filepath, CURRENT_CHAT_HISTORY)
            print(colors.red(f"\nSaved current saved history to {cha_filepath}"))
            continue

        detected_urls = len(scraper.extract_urls(message))
        if detected_urls > 0:
            du_print = f"{detected_urls} URL"
            if detected_urls > 1:
                du_print = f"{detected_urls} URLs"
            du_user = input(
                colors.red(f"{du_print} detected, continue web scraping (y/n)? ")
            )
            if du_user.lower() == "y" or du_user.lower() == "yes":
                print(colors.magenta("\n\n--- BROWSING THE WEB ---\n"))
                message = scraper.scraped_prompt(message)
            print()

        # exit if no prompt is provided
        if len(message) == 0:
            raise KeyboardInterrupt

        messages.append({"role": "user", "content": message})

        obj_chat_history = {"time": time.time(), "user": message, "bot": ""}
        try:
            response = client.chat.completions.create(
                model=selected_model, messages=messages, stream=True
            )

            for chunk in response:
                chunk_message = chunk.choices[0].delta.content
                if chunk_message:
                    last_line = chunk_message
                    sys.stdout.write(colors.green(chunk_message))
                    obj_chat_history["bot"] += chunk_message
                    sys.stdout.flush()

            chat_message = chunk.choices[0].delta.content
            if chat_message:
                messages.append({"role": "assistant", "content": chat_message})
        except Exception as e:
            print(colors.red(f"Error during chat: {e}"))
            break

        CURRENT_CHAT_HISTORY.append(obj_chat_history)


def basic_chat(filepath, model, justString=None):
    try:
        print_padding = False

        if justString == None:
            if "/" not in filepath:
                filepath = os.path.join(os.getcwd(), filepath)

            if os.path.exists(filepath) == False:
                print(colors.red(f"The following file does not exist: {filepath}"))
                return

            print(
                colors.blue(
                    f"Feeding the following file content to {model}:\n{filepath}\n"
                )
            )

            content = "\n".join(youtube.read_file(filepath))
        else:
            content = justString
            print_padding = True

        if print_padding:
            print()

        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": config.INITIAL_PROMPT},
                {"role": "system", "content": content},
            ],
            stream=True,
        )

        last_line = ""
        complete_output = ""
        for chunk in response:
            chunk_message = chunk.choices[0].delta.content
            if chunk_message:
                last_line = chunk_message
                complete_output += chunk_message
                sys.stdout.write(colors.green(chunk_message))
                sys.stdout.flush()

        CURRENT_CHAT_HISTORY.append(
            {"time": time.time(), "user": content, "bot": complete_output}
        )

        if last_line.startswith("\n") == False:
            print()

        if print_padding:
            print()
    except Exception as e:
        print(colors.red(f"Error during chat: {e}"))


def cli():
    try:
        parser = argparse.ArgumentParser(description="Chat with an OpenAI GPT model.")
        parser.add_argument(
            "-tp", "--titleprint", help="Print initial title during interactive mode"
        )
        parser.add_argument(
            "-m", "--model", help="Model to use for chatting", required=False
        )
        parser.add_argument(
            "-f",
            "--file",
            help="Filepath to file that will be sent to the model (text only)",
            required=False,
        )
        parser.add_argument(
            "-s",
            "--string",
            help="None interactive mode, just feed a string into the model",
        )

        args = parser.parse_args()

        title_print_value = True
        if str(args.titleprint).lower() == "false":
            title_print_value = False

        selected_model = args.model

        if selected_model == None:
            openai_models = list_models()
            print(colors.yellow("Available OpenAI Models:"))
            max_length = max(len(model_id) for model_id, _ in openai_models)
            openai_models = sorted(openai_models, key=lambda x: x[1])
            for model_id, created in openai_models:
                formatted_model_id = model_id.ljust(max_length)
                print(
                    colors.yellow(f"   > {formatted_model_id}   {simple_date(created)}")
                )
            print()

            try:
                selected_model = input("Which model do you want to use? ")
                if selected_model not in [model[0] for model in openai_models]:
                    print(colors.red("Invalid model selected. Exiting."))
                    return
            except KeyboardInterrupt:
                return
            print()

        if args.string and args.file:
            print(
                colors.red(
                    f"You can't use the string and file option at the same time!"
                )
            )
        elif args.string:
            basic_chat(None, selected_model, str(args.string))
        elif args.file:
            basic_chat(args.file, selected_model)
        else:
            try:
                chatbot(selected_model, title_print_value)
            except KeyboardInterrupt:
                print()
                sys.exit(0)

    except Exception as err:
        pass
