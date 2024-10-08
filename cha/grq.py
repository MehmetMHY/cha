import os
import sys
import time
import argparse
from typing import List, Dict, Any
import json

from groq import Groq
from cha import colors


client = Groq(api_key=os.environ.get("GROQ_API_KEY"))


def get_models() -> List[Dict[str, Any]]:
    """
    Retrieve available models from Groq API, excluding specified models.

    :return: List of available models
    """

    # NOTE: not all Groq models are text based
    # NOTE: last updated on July 26, 2024
    invalid_model_prefixes = ["whisper", "distil-whisper"]

    response = client.models.list()

    filtered_models = [
        model.to_dict()
        for model in response.data
        if not any(
            model.id.lower().startswith(prefix.lower())
            for prefix in invalid_model_prefixes
        )
    ]

    filtered_models = sorted(filtered_models, key=lambda x: x["id"])

    return filtered_models


def create_chat_completion(model: str, messages: List[Dict[str, str]]) -> str:
    """
    Create a streaming chat completion using the specified Groq model.

    :param model: The model to use
    :param messages: List of message dictionaries
    :return: Generated text
    """
    full_response = ""
    for chunk in client.chat.completions.create(
        model=model, messages=messages, stream=True
    ):
        if chunk.choices[0].delta.content is not None:
            content = chunk.choices[0].delta.content
            print(colors.green(content), end="", flush=True)
            full_response += content
    print()  # Add a newline after the full response
    return full_response


def format_message(role: str, content: str) -> Dict[str, str]:
    """
    Format a message according to Groq API requirements.

    :param role: The role of the message sender ('user' or 'assistant')
    :param content: The content of the message
    :return: Formatted message dictionary
    """
    return {"role": role, "content": content}


def validate_environment() -> None:
    """
    Validate that the necessary environment variables are set.

    :raises EnvironmentError: If the required API key is not set
    """
    if "GROQ_API_KEY" not in os.environ:
        raise EnvironmentError("GROQ_API_KEY environment variable is not set")


def title_print(selected_model: str):
    print(
        colors.yellow(
            f"""
Chatting With Groq's '{selected_model}' Model
 - 'exit' to exit
 - 'multi' for multi-line mode
 - 'done' to end in multi-line mode
 - 'clear' to clear chat history
""".strip()
        )
    )


def chatbot(selected_model: str, print_title: bool = True):
    validate_environment()
    messages = []
    multi_line_input = False
    first_loop = True

    if print_title:
        title_print(selected_model)
    else:
        print()

    while True:
        if not first_loop:
            print()

        user_input_string = colors.blue("User: ")
        if multi_line_input:
            print(
                colors.yellow(
                    "Entered multi-line input mode. Type 'done' to send message"
                )
            )
            user_input_string = colors.red("[M] ") + colors.blue("User: ")

        print(colors.blue(user_input_string), end="", flush=True)
        user_input = input()

        if user_input.lower() == "exit":
            break
        elif user_input.lower() == "multi":
            multi_line_input = True
            continue
        elif user_input.lower() == "clear":
            messages = []
            print(colors.yellow("\nChat history cleared.\n"))
            first_loop = True
            continue

        if multi_line_input:
            message_lines = [user_input]
            while True:
                line = input()
                if line.lower() == "done":
                    break
                message_lines.append(line)
            user_input = "\n".join(message_lines)
            multi_line_input = False

        if len(user_input) == 0:
            continue

        messages.append(format_message("user", user_input))

        print()  # Add a newline before the assistant's response
        try:
            bot_response = create_chat_completion(selected_model, messages)
            messages.append(format_message("assistant", bot_response))
        except Exception as e:
            print(colors.red(f"\nError during chat: {e}"))
            break

        first_loop = False


def process_file(filepath: str, model: str):
    """
    Process a file and send its content to the model.

    :param filepath: Path to the file to be processed
    :param model: Model to use for processing
    """
    try:
        if not os.path.exists(filepath):
            print(colors.red(f"The following file does not exist: {filepath}"))
            return

        print(
            colors.blue(f"Feeding the following file content to {model}:\n{filepath}\n")
        )

        with open(filepath, "r") as file:
            content = file.read()

        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": content},
        ]

        create_chat_completion(model, messages)

    except Exception as e:
        print(colors.red(f"Error processing file: {e}"))


def process_string(input_string: str, model: str):
    """
    Process a string input and send it to the model.

    :param input_string: String to be processed
    :param model: Model to use for processing
    """
    try:
        print()

        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": input_string},
        ]

        create_chat_completion(model, messages)

    except Exception as e:
        print(colors.red(f"Error processing string: {e}"))


def cli():
    parser = argparse.ArgumentParser(description="Chat with Groq models.")
    parser.add_argument("-m", "--model", help="Model to use for chatting")
    parser.add_argument(
        "-tp",
        "--titleprint",
        help="Print initial title during interactive mode",
        action="store_true",
    )
    parser.add_argument(
        "-f",
        "--file",
        help="Filepath to file that will be sent to the model (text only)",
        required=False,
    )
    parser.add_argument(
        "-s", "--string", help="Non-interactive mode, just feed a string into the model"
    )
    args = parser.parse_args()

    selected_model = args.model
    print_title = args.titleprint

    if not selected_model:
        models = get_models()
        print(colors.yellow("Available Groq Models:"))
        for i, model in enumerate(models, 1):
            print(colors.yellow(f"   {i}) {model['id']}"))
        print()

        try:
            model_choice = int(input(colors.blue("Model (Enter the number): ")))
            if 1 <= model_choice <= len(models):
                selected_model = models[model_choice - 1]["id"]
            else:
                print(colors.red("Invalid model selected. Exiting."))
                return
        except ValueError:
            print(colors.red("Invalid input. Exiting."))
            return
        except KeyboardInterrupt:
            return
        print()

    try:
        if args.file and args.string:
            print(
                colors.red("You can't use the string and file option at the same time!")
            )
        elif args.file:
            process_file(args.file, selected_model)
        elif args.string:
            process_string(args.string, selected_model)
        else:
            chatbot(selected_model, print_title)
    except KeyboardInterrupt:
        print()
        sys.exit(0)


if __name__ == "__main__":
    try:
        cli()
    except KeyboardInterrupt:
        pass
