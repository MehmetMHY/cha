import argparse
import datetime
import time
import sys
import os

# NOTE: make sure environment variable is defined before doing anything
if 'OPENAI_API_KEY' not in os.environ:
    print("The OPENAI_API_KEY env variable is not defined. Grab your API key at: https://platform.openai.com/api-keys")
    sys.exit(1)

# 3rd party packages
from openai import OpenAI
from cha import scrapper, youtube, colors, image, search

# hard coded config variables
INITIAL_PROMPT = "You are a helpful assistant who keeps your response short and to the point."
MULTI_LINE_SEND = "END"
MULI_LINE_MODE_TEXT = "!m"
CLEAR_HISTORY_TEXT = "!c"
IMG_GEN_MODE = "!i"
SAVE_CHAT_HISTORY = "!s"
EXIT_STRING_KEY = "!e"
ADVANCE_SEARCH_KEY = "!b"

# important global variables
CURRENT_CHAT_HISTORY = []

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
            raise ValueError('No models available')

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
    # last updated: 3-15-2024
    print(colors.yellow(f"""Chatting With OpenAI's '{selected_model}' Model
 - '{EXIT_STRING_KEY}' or CTRL-C to exit
 - '{MULI_LINE_MODE_TEXT}' for single/multi-line mode
 - '{MULTI_LINE_SEND}' to end in multi-line mode
 - '{CLEAR_HISTORY_TEXT}' to clear chat history
 - '{IMG_GEN_MODE}' for image generation
 - '{SAVE_CHAT_HISTORY}' to save chat history
 - '{ADVANCE_SEARCH_KEY}' for answer-search""").strip())

def chatbot(selected_model):
    messages = [{"role": "system", "content": INITIAL_PROMPT}]
    multi_line_input = False

    # print the initial title
    title_print(selected_model)

    first_loop = True
    last_line = ""
    while True:
        if first_loop == False:
            print()

        if last_line.endswith('\n') == False:
            print()

        print(colors.blue("User: "), end="", flush=True)

        first_loop = False

        if not multi_line_input:
            message = sys.stdin.readline().rstrip('\n')
            
            if message == MULI_LINE_MODE_TEXT:
                multi_line_input = True
                print(colors.yellow(f"\n\nSwitched to multi-line input mode. Type '{MULTI_LINE_SEND}' to send message."))
                continue
            elif message.replace(" ", "") == IMG_GEN_MODE:
                print("\n")
                image.gen_image()
                continue
            elif message.replace(" ", "") == EXIT_STRING_KEY.lower():
                break
            elif message.replace(" ", "") == CLEAR_HISTORY_TEXT:
                messages = [{"role": "system", "content": INITIAL_PROMPT}]
                print(colors.yellow("\n\nChat history cleared.\n"))
                first_loop = True
                continue
        
        if multi_line_input:
            message_lines = []
            while True:
                line = sys.stdin.readline().rstrip('\n')
                if line == MULI_LINE_MODE_TEXT:
                    multi_line_input = False
                    print(colors.yellow("\n\nSwitched to single-line input mode."))
                    break
                elif line.lower() == MULTI_LINE_SEND.lower():
                    break
                message_lines.append(line)
            message = '\n'.join(message_lines)
            if message.upper() == CLEAR_HISTORY_TEXT:
                messages = [{"role": "system", "content": INITIAL_PROMPT}]
                print(colors.yellow("\n\nChat history cleared.\n"))
                first_loop = True
                continue
            if not multi_line_input:
                continue

        # NOTE: this is annoying, but we have to account for this :(
        print()

        if message.startswith(ADVANCE_SEARCH_KEY):
            try:
                asq = " ".join(message.replace(ADVANCE_SEARCH_KEY, "").split())
                # NOTE: the question most be greater then 2 words atleast
                if len(asq) >= 5 and len(asq.split(" ")) >= 3:
                    print("\n")
                    aso = search.answer_search(asq, print_mode=True)
                    CURRENT_CHAT_HISTORY.append({ "time": time.time(), "user": asq, "bot": aso })
                    print()
                else:
                    print(colors.red(f"\nFor An Answer-Search, your question MOST be atleast 3 words long"))
            except Exception as err:
                print(colors.red(f"Failed to run Answer-Search due to: {err}\n"))
            continue

        if message == SAVE_CHAT_HISTORY:
            cha_filepath = f"cha_{int(time.time())}.txt"
            youtube.write_json(cha_filepath, CURRENT_CHAT_HISTORY)
            print(colors.red(f"\nSaved current saved history to {cha_filepath}"))
            continue
        
        detected_urls = len(scrapper.extract_urls(message))
        if detected_urls > 0:
            du_print = f"{detected_urls} URL"
            if detected_urls > 1:
                du_print = f"{detected_urls} URLs"
            du_user = input(colors.red(f"{du_print} detected, continue web scrapping (y/n)? "))
            if du_user.lower() == "y" or du_user.lower() == "yes":
                print(colors.magenta("\n\n--- BROWSING THE WEB ---\n"))
                message = scrapper.scrapped_prompt(message)
            print()

        # exit if no prompt is provided
        if len(message) == 0:
            raise KeyboardInterrupt

        messages.append({"role": "user", "content": message})

        obj_chat_history = { "time": time.time(), "user": message, "bot": "" }
        try:
            response = client.chat.completions.create(
                model=selected_model,
                messages=messages,
                stream=True
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

            print(colors.blue(f"Feeding the following file content to {model}:\n{filepath}\n"))

            content = "\n".join(
                youtube.read_file(filepath)
            )
        else:
            content = justString
            print_padding = True

        if print_padding:
            print()

        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": INITIAL_PROMPT},
                {"role": "system", "content": content},
            ],
            stream=True
        )

        last_line = ""
        for chunk in response:
            chunk_message = chunk.choices[0].delta.content
            if chunk_message:
                last_line = chunk_message
                sys.stdout.write(colors.green(chunk_message))
                sys.stdout.flush()

        if last_line.startswith("\n") == False:
            print()

        if print_padding:
            print()
    except Exception as e:
        print(colors.red(f"Error during chat: {e}"))

def cli():
    try:
        parser = argparse.ArgumentParser(description="Chat with an OpenAI GPT model.")
        parser.add_argument('-m', '--model', help='Model to use for chatting', required=False)
        parser.add_argument('-f', '--file', help='Filepath to file that will be sent to the model (text only)', required=False)
        parser.add_argument('-s', '--string', help='None interactive mode, just feed a string into the model')

        args = parser.parse_args()

        openai_models = list_models()

        if args.model and any(model[0] == args.model for model in openai_models):
            selected_model = args.model
        else:
            print(colors.yellow("Available OpenAI Models:"))
            max_length = max(len(model_id) for model_id, _ in openai_models)
            openai_models = sorted(openai_models, key=lambda x: x[1])
            for model_id, created in openai_models:
                formatted_model_id = model_id.ljust(max_length)
                print(colors.yellow(f"   > {formatted_model_id}   {simple_date(created)}"))
            print()

            try:
                selected_model = input("Which model do you want to use? ")
            except KeyboardInterrupt:
                return
            print()

        if selected_model not in [model[0] for model in openai_models]:
            print(colors.red("Invalid model selected. Exiting."))
            return
        
        if args.string and args.file:
            print(colors.red(f"You can't use the string and file option at the same time!"))
            return
        
        if args.string:
            basic_chat(None, selected_model, str(args.string))
            return

        if args.file:
            basic_chat(args.file, selected_model)
            return

        try:
            chatbot(selected_model)
        except:
            pass
    except:
        pass

