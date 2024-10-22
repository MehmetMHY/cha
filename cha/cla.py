import argparse, json, time, sys, os, re
from anthropic import Anthropic
from bs4 import BeautifulSoup
from cha import colors, config, scraper, utils

utils.check_env_variable("ANTHROPIC_API_KEY", config.ANTHROPIC_DOCS_LINK)

client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
CURRENT_CHAT_HISTORY = [{"time": time.time(), "user": config.INITIAL_PROMPT, "bot": ""}]


# NOTE: (6-30-2024) Anthropic's API lacks an endpoint for fetching the latest supported models, so web scraping is required
def get_anthropic_models():
    try:
        url = "https://docs.anthropic.com/en/docs/about-claude/models"

        response = utils.get_request(url=url)
        if response == None:
            raise Exception(f"Failed to make HTTP GET request to {url}")

        soup = BeautifulSoup(response.content, "html.parser")

        output = []
        for table in soup.find_all("table")[:6]:
            headers = [header.text.strip() for header in table.find_all("th")]
            for row in table.find_all("tr")[1:]:
                data = dict(
                    zip(headers, [cell.text.strip() for cell in row.find_all("td")])
                )
                if "Model" in data and "Anthropic API" in data:
                    if not any(
                        phrase in data["Anthropic API"].lower()
                        for phrase in ["coming soon", "later this year"]
                    ):
                        output.append(
                            {"name": data["Model"], "model": data["Anthropic API"]}
                        )

        if not all(
            isinstance(d, dict)
            and all(key in d and d[key] for key in ["name", "model"])
            for d in output
        ):
            raise Exception("model scraper is broken")

        # (10-22-2024) account for cases like this: "claude-3-5-sonnet-20241022 (claude-3-5-sonnet-latest)" -> "claude-3-5-sonnet-20241022"
        for entry in output:
            entry["model"] = re.sub(r"[\s\n]+", "", str(entry["model"].split(" (")[0]))

        return output
    except Exception as err:
        return str(err)


def chat(model, message, stream=True):
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
            return response.content[0].text
    except KeyboardInterrupt:
        print()
        sys.exit(1)
    except Exception as e:
        return f"Error: {e}"


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
            f" - Type '{config.MULI_LINE_MODE_TEXT}' for multi-line mode.\n"
            f" - Type '{config.MULTI_LINE_SEND}' to exit multi-line mode.\n"
            f" - Type '{config.CLEAR_HISTORY_TEXT}' to clear chat history.\n"
            f" - Type '{config.SAVE_CHAT_HISTORY}' to save chat history.\n"
            f" - Type '{config.HELP_PRINT_OPTIONS_KEY}' to list all options"
        )
    )


def interactive_chat(model, print_title):
    global CURRENT_CHAT_HISTORY
    if print_title:
        title_print(model)
    while True:
        user_input = utils.safe_input(colors.blue("User: ")).strip()
        if user_input == config.EXIT_STRING_KEY:
            break

        if user_input == config.MULI_LINE_MODE_TEXT:
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

        detected_urls = len(scraper.extract_urls(user_input))
        if detected_urls > 0:
            du_print = f"{detected_urls} URL{'s' if detected_urls > 1 else ''}"
            du_user = input(
                colors.red(f"{du_print} detected, continue web scraping (y/n)? ")
            )
            if du_user.lower() == "y" or du_user.lower() == "yes":
                user_input = scraper.scraped_prompt(user_input)

        CURRENT_CHAT_HISTORY.append(
            {"time": time.time(), "user": user_input, "bot": ""}
        )
        response = chat(model, user_input)
        CURRENT_CHAT_HISTORY[-1]["bot"] = response


def user_select_model():
    models = get_anthropic_models()
    if type(models) == str:
        print(colors.red(f"Failed to get models"))
        sys.exit(1)
    print(colors.yellow("Available Anthropic Models:"))
    for i, model in enumerate(models, 1):
        print(colors.yellow(f"   {i}) {model['name']} ({model['model']})"))
    choice = int(utils.safe_input(colors.blue("Select model number: ")))
    return models[choice - 1]["model"]


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

    selected_model = args.model
    if args.select_model:
        selected_model = user_select_model()

    if args.file and args.string:
        print(colors.red("You can't use the string and file option at the same time!"))
    elif args.file:
        with open(args.file, "r") as file:
            content = file.read()
        chat(selected_model, content, stream=True)
    elif args.string:
        chat(selected_model, (" ".join(args.string)), stream=True)
    else:
        interactive_chat(selected_model, (args.print_title))
