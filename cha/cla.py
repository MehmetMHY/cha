import argparse
import json
import time
import sys
import os

from anthropic import Anthropic
from cha import colors, config, scrapper

# global variables
CURRENT_CHAT_HISTORY = [{"time": time.time(), "user": config.INITIAL_PROMPT, "bot": ""}]
client = Anthropic(
    api_key=os.environ.get("ANTHROPIC_API_KEY"),
)


def title_print(selected_model):
    print(
        colors.yellow(
            f"""
Chatting With Anthropic's '{selected_model}' Model
 - '{config.EXIT_STRING_KEY}' to exit
 - '{config.MULI_LINE_MODE_TEXT}' for multi-line mode
 - '{config.MULTI_LINE_SEND}' to end in multi-line mode
 - '{config.CLEAR_HISTORY_TEXT}' to clear chat history
 - '{config.SAVE_CHAT_HISTORY}' to save chat history
    """.strip()
        )
    )


def chatbot(selected_model, print_title=True):
    messages = []
    multi_line_input = False
    first_loop = True

    if print_title:
        title_print(selected_model)

    line_mode = False
    last_line = ""
    while True:
        if not first_loop:
            print()

        if not last_line.endswith("\n"):
            print()

        user_input_string = colors.blue("User: ")
        if line_mode:
            print(
                colors.yellow(
                    f"Entered multi-line input mode. Type '{config.MULTI_LINE_SEND}' to send message"
                )
            )
            user_input_string = colors.red("[M] ") + colors.blue("User: ")
        print(user_input_string, end="", flush=True)

        first_loop = False

        if not multi_line_input:
            message = sys.stdin.readline().rstrip("\n")

            if message == config.MULI_LINE_MODE_TEXT:
                multi_line_input = True
                line_mode = True
                last_line = "\n"
                continue
            elif message.replace(" ", "") == config.EXIT_STRING_KEY:
                break
            elif message.replace(" ", "") == config.CLEAR_HISTORY_TEXT:
                messages = []
                print(colors.yellow("\n\nChat history cleared.\n"))
                first_loop = True
                continue

        if multi_line_input:
            message_lines = []
            while True:
                line = sys.stdin.readline().rstrip("\n")
                if line == config.MULTI_LINE_SEND:
                    break
                elif line.replace(" ", "") == config.CLEAR_HISTORY_TEXT:
                    messages = []
                    print(colors.yellow("\nChat history cleared.\n"))
                    first_loop = True
                    break
                message_lines.append(line)
            message = "\n".join(message_lines)
            line_mode = False
            multi_line_input = False

        print()

        if message == config.SAVE_CHAT_HISTORY:
            cha_filepath = f"cha_{int(time.time())}.json"
            with open(cha_filepath, "w") as f:
                json.dump(CURRENT_CHAT_HISTORY, f)
            print(colors.red(f"\nSaved current chat history to {cha_filepath}"))
            continue

        if len(message) == 0:
            raise KeyboardInterrupt

        messages.append({"role": "user", "content": message})

        obj_chat_history = {"time": time.time(), "user": message, "bot": ""}
        try:
            response = client.messages.create(
                model=selected_model,
                max_tokens=1024,
                messages=messages,
                system=config.INITIAL_PROMPT,
                stream=True,
            )

            for chunk in response:
                if chunk.type == "content_block_delta":
                    last_line = chunk.delta.text
                    sys.stdout.write(colors.green(chunk.delta.text))
                    obj_chat_history["bot"] += chunk.delta.text
                    sys.stdout.flush()

            messages.append({"role": "assistant", "content": obj_chat_history["bot"]})
        except Exception as e:
            print(colors.red(f"Error during chat: {e}"))
            break

        CURRENT_CHAT_HISTORY.append(obj_chat_history)


def basic_chat(filepath, model, just_string=None):
    try:
        print_padding = False

        if just_string is None:
            if "/" not in filepath:
                filepath = os.path.join(os.getcwd(), filepath)

            if not os.path.exists(filepath):
                print(colors.red(f"The following file does not exist: {filepath}"))
                return

            print(
                colors.blue(
                    f"Feeding the following file content to {model}:\n{filepath}\n"
                )
            )

            with open(filepath, "r") as file:
                content = file.read()
        else:
            content = just_string
            print_padding = True

        if print_padding:
            print()

        response = client.messages.create(
            model=model,
            max_tokens=1024,
            messages=[{"role": "user", "content": content}],
            system=config.INITIAL_PROMPT,
            stream=True,
        )

        last_line = ""
        complete_output = ""
        for chunk in response:
            if chunk.type == "content_block_delta":
                last_line = chunk.delta.text
                complete_output += chunk.delta.text
                sys.stdout.write(colors.green(chunk.delta.text))
                sys.stdout.flush()

        CURRENT_CHAT_HISTORY.append(
            {"time": time.time(), "user": content, "bot": complete_output}
        )

        if not last_line.startswith("\n"):
            print()

        if print_padding:
            print()
    except Exception as e:
        print(colors.red(f"Error during chat: {e}"))


def cli():
    try:
        parser = argparse.ArgumentParser(
            description="Chat with an Anthropic Claude model."
        )
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
            help="Non-interactive mode, just feed a string into the model",
        )

        args = parser.parse_args()

        title_print_value = True
        if str(args.titleprint).lower() == "false":
            title_print_value = False

        selected_model = args.model

        if selected_model == None:
            anthropic_models = scrapper.get_anthropic_models()
            print(colors.yellow("Available Anthropic Models:"))
            for i, model in enumerate(anthropic_models, 1):
                print(colors.yellow(f"   {i}) {model['name']} ({model['model']})"))
            print()

            try:
                model_choice = int(input(colors.blue("Model (Enter the number): ")))
                if 1 <= model_choice <= len(anthropic_models):
                    selected_model = anthropic_models[model_choice - 1]["model"]
                else:
                    print(colors.red("Invalid model selected. Exiting."))
                    return
            except ValueError:
                print(colors.red("Invalid input. Exiting."))
                return
            except KeyboardInterrupt:
                return
            print()

        if args.string and args.file:
            print(
                colors.red("You can't use the string and file option at the same time!")
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
        print(colors.red(f"An error occurred: {err}"))


if __name__ == "__main__":
    if scrapper.test_scrapper_get_anthropic_models() == False:
        print(colors.red(f"Models' name scrapper is broken"))
        sys.exit(1)
    cli()
