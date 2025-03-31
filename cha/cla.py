import argparse
import json
import time
import sys
import os

from cha import config, colors, scraper, utils, loading
from anthropic import Anthropic

# add on to the main config
config.ANTHROPIC_DOCS_LINK = "https://docs.anthropic.com/en/docs/welcome"
config.CLA_DEFAULT_MODEL = "claude-3-7-sonnet-20250219"
config.CLA_MAX_TOKENS = 64_000


CURRENT_CHAT_HISTORY = [{"time": time.time(), "user": config.INITIAL_PROMPT, "bot": ""}]


def chat(client, model, message, stream=True):
    try:
        messages = [
            {"role": "user", "content": msg["user"]}
            for msg in CURRENT_CHAT_HISTORY[:-1]
        ]

        messages.append({"role": "user", "content": message})

        response = client.messages.create(
            model=model,
            max_tokens=config.CLA_MAX_TOKENS,
            messages=messages,
            system=config.INITIAL_PROMPT,
            stream=stream,
        )
        if stream:
            full_response = ""
            for chunk in response:
                if chunk.type == "content_block_delta":
                    sys.stdout.write(colors.green(chunk.delta.text))
                    sys.stdout.flush()
                    full_response += chunk.delta.text
            print()
            return full_response
        else:
            # non-streamed response
            return response.content[0].text
    except KeyboardInterrupt:
        print()
        sys.exit(1)
    except Exception as e:
        return {"error": str(e)}


def get_multi_line_input():
    print(
        colors.yellow(
            f"Entered multi-line input mode. Type '{config.MULTI_LINE_SEND}' to send message"
        )
    )
    lines = []
    input_print = colors.red("[M] ") + colors.blue("User: ")
    while True:
        line = utils.safe_input(input_print).rstrip("\n")
        if line == config.MULTI_LINE_SEND:
            break
        lines.append(line)
        input_print = ""
    return "\n".join(lines)


def title_print(selected_model):
    print(
        colors.yellow(
            f"Chatting with Anthropic's '{selected_model}' Model\n"
            f" - Type '{config.EXIT_STRING_KEY}' to exit.\n"
            f" - Type '{config.MULTI_LINE_MODE_TEXT}' for multi-line mode.\n"
            f" - Type '{config.MULTI_LINE_SEND}' to exit multi-line mode.\n"
            f" - Type '{config.CLEAR_HISTORY_TEXT}' to clear chat history.\n"
            f" - Type '{config.SAVE_CHAT_HISTORY}' to save chat history.\n"
            f" - Type '{config.HELP_PRINT_OPTIONS_KEY}' to list all options"
        )
    )


def interactive_chat(client, model, print_title):
    """
    Runs an interactive REPL-style chat with the given model.
    """
    global CURRENT_CHAT_HISTORY

    if print_title:
        title_print(model)

    while True:
        user_input = utils.safe_input(colors.blue("User: ")).strip()

        if user_input == config.EXIT_STRING_KEY:
            break

        if user_input == config.MULTI_LINE_MODE_TEXT:
            user_input = get_multi_line_input()

        if user_input.replace(" ", "") == config.CLEAR_HISTORY_TEXT:
            CURRENT_CHAT_HISTORY = [
                {"time": time.time(), "user": config.INITIAL_PROMPT, "bot": ""}
            ]
            print(colors.yellow("Chat history cleared"))
            continue

        if user_input == config.SAVE_CHAT_HISTORY:
            cla_filepath = f"cla_{int(time.time())}.json"
            with open(cla_filepath, "w") as f:
                json.dump(CURRENT_CHAT_HISTORY, f, indent=4)
            print(colors.red(f"Saved current chat history to {cla_filepath}"))
            continue

        if user_input == config.HELP_PRINT_OPTIONS_KEY:
            title_print(model)
            continue

        if user_input == config.TEXT_EDITOR_INPUT_MODE:
            editor_content = utils.check_terminal_editors_and_edit()
            if editor_content is None:
                print(colors.red(f"No text editor available or editing cancelled"))
                continue
            if len(editor_content) == 0:
                continue
            for line in str(editor_content).rstrip("\n").split("\n"):
                print(colors.blue(">"), line)
            user_input = editor_content

        detected_urls = len(scraper.extract_urls(user_input))
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
                    user_input = scraper.scraped_prompt(user_input)
                finally:
                    loading.stop_loading()

        CURRENT_CHAT_HISTORY.append(
            {"time": time.time(), "user": user_input, "bot": ""}
        )

        response = chat(client, model, user_input)
        if isinstance(response, dict) and response.get("error") is not None:
            print(colors.red(response["error"]))
            continue

        CURRENT_CHAT_HISTORY[-1]["bot"] = response


def user_select_model(client):
    models = [
        {"model": model.id, "name": model.display_name}
        for model in client.models.list()
    ]
    if isinstance(models, str):
        print(colors.red("Failed to get models"))
        sys.exit(1)

    print(colors.yellow("Available Anthropic Models:"))
    for i, model_dict in enumerate(models, 1):
        print(colors.yellow(f"   {i}) {model_dict['name']} ({model_dict['model']})"))

    choice = int(utils.safe_input(colors.blue("Select model number: ")))
    return models[choice - 1]["model"]


def anthropic(
    selected_model=config.CLA_DEFAULT_MODEL,
    file=None,
    string=None,
    print_title=False,
    client=None,
):
    utils.check_env_variable("ANTHROPIC_API_KEY", config.ANTHROPIC_DOCS_LINK)

    if client is None:
        client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    if selected_model == None:
        selected_model = user_select_model(client)

    if file and string:
        print(colors.red("You can't use the string and file option at the same time!"))
        return

    if file:
        with open(file, "r") as f:
            content = f.read()
        chat(client, selected_model, content, stream=True)
    elif string:
        chat(client, selected_model, " ".join(string), stream=True)
    else:
        interactive_chat(client, selected_model, print_title)


def cli():
    parser = argparse.ArgumentParser(description="Chat with an Anthropic Claude model.")
    parser.add_argument(
        "-m",
        "--model",
        help="Model to use for chatting",
        default=config.CLA_DEFAULT_MODEL,
    )
    parser.add_argument(
        "-sm",
        "--select_model",
        help="Select one model from Anthropic's supported models",
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
        "-pt",
        "--print_title",
        help="Print initial title during interactive mode",
        action="store_true",
    )
    args = parser.parse_args()

    selected_model_name = args.model
    if args.select_model:
        selected_model_name = None

    anthropic(
        selected_model=selected_model_name,
        file=args.file,
        string=args.string,
        print_title=args.print_title,
    )

    return


if __name__ == "__main__":
    cli()
