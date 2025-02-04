import argparse
import json
import time
import sys
import os

from together import Together
from cha import colors, config, scraper, utils


# Global chat history
CURRENT_CHAT_HISTORY = [{"time": time.time(), "user": config.INITIAL_PROMPT, "bot": ""}]


# Check for Together API key before continuing.
utils.check_env_variable("TOGETHER_API_KEY", config.TOGETHER_DOCS_LINK)


def together_models():
    """
    Fetch available Together models.
    Returns a dict mapping model id to model details.
    """

    try:
        response = utils.get_request(
            url="https://api.together.xyz/v1/models",
            headers={
                "accept": "application/json",
                "authorization": f"Bearer {os.environ.get('TOGETHER_API_KEY')}",
            },
        )
        response.raise_for_status()
    except Exception as err:
        print(colors.red(f"Error fetching models: {err}"))
        sys.exit(1)

    output = {}
    try:
        models_list = json.loads(response.text)
        for entry in models_list:
            if entry["type"] != "chat":
                continue
            output[entry["id"]] = entry
    except Exception as err:
        print(colors.red(f"Error parsing models: {err}"))
        sys.exit(1)
    return output


# Instantiate Together client
client = Together()


def chat(model, message, stream=True):
    """
    Send a message to Together's chat API using the provided model.
    Builds a conversation from the global CURRENT_CHAT_HISTORY.
    """
    try:
        # Build messages list (using only user messages, similar to the Claude code)
        messages = [
            {"role": "user", "content": msg["user"]}
            for msg in CURRENT_CHAT_HISTORY[:-1]
        ]
        messages.append({"role": "user", "content": message})

        response = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=config.TOGETHER_MAX_TOKENS,
            temperature=config.TOGETHER_TEMPERATURE,
            top_p=config.TOGETHER_TOP_P,
            top_k=config.TOGETHER_TOP_K,
            repetition_penalty=config.TOGETHER_REPETITION_PENALTY,
            stream=stream,
        )

        if stream:
            full_response = ""
            try:
                for chunk in response:
                    if chunk.choices and len(chunk.choices) > 0:
                        content = chunk.choices[0].delta.content
                        if content:
                            sys.stdout.write(colors.green(content))
                            sys.stdout.flush()
                            full_response += content
            except (KeyboardInterrupt, EOFError):
                # User interrupted streaming; exit streaming gracefully.
                print()  # Ensure newline is printed.
                return full_response
            print()  # Newline after streaming is done.
            return full_response
        else:
            return response.content[0].text
    except Exception as e:
        # Avoid printing large tracebacks.
        print(colors.red("An error occurred during chat."))
        return {"error": str(e)}


def get_multi_line_input():
    """
    Allow the user to type multiple lines.
    User types config.MULTI_LINE_SEND on a line by itself to finish.
    """
    print(
        colors.yellow(
            f"Entered multi-line input mode. Type '{config.MULTI_LINE_SEND}' on a line by itself to send your message."
        )
    )
    lines = []
    prompt_str = colors.red("[M] ") + colors.blue("User: ")
    while True:
        try:
            line = input(prompt_str)
        except (KeyboardInterrupt, EOFError):
            print()  # Print newline on interrupt.
            break
        line = line.rstrip("\n")
        if line.strip() == config.MULTI_LINE_SEND:
            break
        lines.append(line)
        prompt_str = ""
    return "\n".join(lines)


def title_print(selected_model):
    """
    Print the header information and available commands.
    """
    print(
        colors.yellow(
            f"Chatting with Together's model '{selected_model}'\n"
            f" - Type '{config.EXIT_STRING_KEY}' to exit.\n"
            f" - Type '{config.MULTI_LINE_MODE_TEXT}' for multi-line mode.\n"
            f" - Type '{config.MULTI_LINE_SEND}' to send your multi-line message.\n"
            f" - Type '{config.CLEAR_HISTORY_TEXT}' to clear chat history.\n"
            f" - Type '{config.SAVE_CHAT_HISTORY}' to save chat history.\n"
            f" - Type '{config.HELP_PRINT_OPTIONS_KEY}' to list all options."
        )
    )


def interactive_chat(model, print_title_flag):
    """
    Run an interactive chat session.
    """
    global CURRENT_CHAT_HISTORY
    if print_title_flag:
        title_print(model)
    while True:
        try:
            user_input = input(colors.blue("User: ")).strip()
        except (KeyboardInterrupt, EOFError):
            print()  # Print newline on interrupt.
            break

        if user_input == config.EXIT_STRING_KEY:
            break

        if user_input == config.MULTI_LINE_MODE_TEXT:
            user_input = get_multi_line_input()

        # --- Scraping Logic ---
        detected_urls = len(scraper.extract_urls(user_input))
        if detected_urls > 0:
            du_print = f"{detected_urls} URL{'s' if detected_urls > 1 else ''}"
            try:
                du_user = input(
                    colors.red(f"{du_print} detected, continue web scraping (y/n)? ")
                )
            except (KeyboardInterrupt, EOFError):
                print()  # Print newline if interrupted.
                continue
            if du_user.lower() in ["y", "yes"]:
                user_input = scraper.scraped_prompt(user_input)
        # -----------------------

        if user_input.replace(" ", "") == config.CLEAR_HISTORY_TEXT:
            CURRENT_CHAT_HISTORY = [
                {"time": time.time(), "user": config.INITIAL_PROMPT, "bot": ""}
            ]
            print(colors.yellow("Chat history cleared."))
            continue

        if user_input == config.SAVE_CHAT_HISTORY:
            filepath = f"together_{int(time.time())}.json"
            try:
                with open(filepath, "w") as f:
                    json.dump(CURRENT_CHAT_HISTORY, f, indent=4)
                print(colors.red(f"Saved current chat history to {filepath}"))
            except Exception as e:
                print(colors.red(f"Error saving chat history: {e}"))
            continue

        if user_input == config.HELP_PRINT_OPTIONS_KEY:
            title_print(model)
            continue

        # Append the new message to the chat history.
        CURRENT_CHAT_HISTORY.append(
            {"time": time.time(), "user": user_input, "bot": ""}
        )
        response = chat(model, user_input)
        if isinstance(response, dict) and response.get("error"):
            print(colors.red(response.get("error")))
            continue

        CURRENT_CHAT_HISTORY[-1]["bot"] = response


def user_select_model():
    """
    Let the user select a model from Together's supported models.
    """
    models = together_models()
    if not models:
        print(colors.red("Failed to get models"))
        sys.exit(1)
    model_list = list(models.values())
    print(colors.yellow("Available Together Models:"))
    for i, m in enumerate(model_list, 1):
        desc = m.get("description", "")
        print(colors.yellow(f"   {i}) {m['id']} {('- ' + desc) if desc else ''}"))
    try:
        choice = int(input(colors.blue("Select model number: ")))
    except (KeyboardInterrupt, EOFError, ValueError):
        print(colors.red("\nInvalid selection."))
        sys.exit(1)
    if choice < 1 or choice > len(model_list):
        print(colors.red("\nInvalid selection."))
        sys.exit(1)
    return model_list[choice - 1]["id"]


def cli():
    """
    Parse command-line arguments and run either non-interactive or interactive chat.
    """
    parser = argparse.ArgumentParser(description="Chat with a Together AI model.")
    parser.add_argument(
        "-m",
        "--model",
        help="Model to use for chatting",
        default=config.TOGETHER_DEFAULT_MODEL,
    )
    parser.add_argument(
        "-sm",
        "--select_model",
        help="Select one model from Together's supported models",
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
        help="Non-interactive mode: feed a string into the model",
    )
    parser.add_argument(
        "-pt",
        "--print_title",
        help="Print initial title during interactive mode",
        action="store_true",
    )
    args = parser.parse_args()

    selected_model = args.model
    if args.select_model:
        selected_model = user_select_model()

    # Non-interactive mode: file or a string provided
    if args.file and args.string:
        print(colors.red("You can't use the string and file option at the same time!"))
        sys.exit(1)
    elif args.file:
        try:
            with open(args.file, "r") as file:
                content = file.read()
        except Exception as e:
            print(colors.red(f"Error reading file: {e}"))
            sys.exit(1)
        chat(selected_model, content, stream=True)
    elif args.string:
        chat(selected_model, " ".join(args.string), stream=True)
    else:
        interactive_chat(selected_model, args.print_title)


if __name__ == "__main__":
    cli()
