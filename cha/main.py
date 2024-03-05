import os
import sys
import argparse
import datetime

# 3rd party packages
from openai import OpenAI
from cha import scrapper, youtube, colors, image

# hard coded config variables
MULI_LINE_MODE_TEXT = "~!"
CLEAR_HISTORY_TEXT = "!CLEAR"
INITIAL_PROMPT = "You are a helpful assistant who keeps your response short and to the point."
IMG_GEN_MODE = "!IMG"

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

def chatbot(selected_model):
    messages = [{"role": "system", "content": INITIAL_PROMPT}]
    multi_line_input = False

    print(colors.blue(f"Start chatting with the {selected_model} model (type 'quit' to stop)! Type '{MULI_LINE_MODE_TEXT}' to switch input mode."))
    print(colors.yellow("\nTip: During the chat, you can switch between single-line and multi-line input modes."))
    print(colors.yellow(f"\nType '{MULI_LINE_MODE_TEXT}' to toggle between these modes. In multi-line mode, type 'END' to send your message. Or type '{CLEAR_HISTORY_TEXT}' to clear the current chat history."))
    print(colors.yellow(f"\nEnter '{IMG_GEN_MODE}' to generate image(s)"))

    first_loop = True
    last_line = ""
    while True:
        if first_loop == False:
            print()

        if last_line.endswith('\n') == False:
            print()

        print("User: ", end="", flush=True)

        first_loop = False

        if not multi_line_input:
            message = sys.stdin.readline().rstrip('\n')
            
            if message == MULI_LINE_MODE_TEXT:
                multi_line_input = True
                print(colors.blue("\n\nSwitched to multi-line input mode. Type 'END' to send message."))
                continue
            elif message.replace(" ", "") == IMG_GEN_MODE:
                print("\n")
                image.gen_image()
                continue
            elif message.lower() == "quit":
                break
            elif message.upper() == CLEAR_HISTORY_TEXT:
                messages = [{"role": "system", "content": INITIAL_PROMPT}]
                print(colors.blue("\n\nChat history cleared.\n"))
                first_loop = True
                continue
        
        if multi_line_input:
            message_lines = []
            while True:
                line = sys.stdin.readline().rstrip('\n')
                if line == MULI_LINE_MODE_TEXT:
                    multi_line_input = False
                    print(colors.blue("\n\nSwitched to single-line input mode."))
                    break
                elif line.lower() == "end":
                    print()
                    break
                message_lines.append(line)
            message = '\n'.join(message_lines)
            if message.upper() == CLEAR_HISTORY_TEXT:
                messages = [{"role": "system", "content": INITIAL_PROMPT}]
                print(colors.blue("\n\nChat history cleared.\n"))
                first_loop = True
                continue
            if not multi_line_input:
                continue

        print()
        
        if len(scrapper.extract_urls(message)) > 0:
            print(colors.magenta("\n--- BROWSING THE WEB ---\n"))
            message = scrapper.scrapped_prompt(message)
            print()

        # exit if no prompt is provided
        if len(message) == 0:
            raise KeyboardInterrupt

        messages.append({"role": "user", "content": message})

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
                    sys.stdout.flush()

            chat_message = chunk.choices[0].delta.content
            if chat_message:
                messages.append({"role": "assistant", "content": chat_message})
        except Exception as e:
            print(colors.red(f"Error during chat: {e}"))
            break

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
