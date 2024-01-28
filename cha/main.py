import openai
import os
import sys
import argparse
import datetime
import subprocess

# hard coded config values
MULI_LINE_MODE_TEXT = "~!"

openai.api_key = os.getenv("OPENAI_API_KEY")

def red(text): return f"\033[91m{text}\033[0m"
def green(text): return f"\033[92m{text}\033[0m"
def yellow(text): return f"\033[93m{text}\033[0m"
def blue(text): return f"\033[94m{text}\033[0m"

def execute(cmd):
    proc = subprocess.Popen(str(cmd), shell=True, stdout=subprocess.PIPE,)
    output = proc.communicate()[0].decode("utf-8")
    return output.split("\n")

def list_models():
    try:
        response = openai.Model.list()
        if not response['data']:
            raise ValueError('No models available')
        openai_models = [(model['id'], model['created']) for model in response['data'] if "gpt" in model['id'] and "instruct" not in model['id']]
        return openai_models
    except Exception as e:
        print(red(f"Error fetching models: {e}"))
        sys.exit(1)

def chatbot(selected_model):
    messages = [{"role": "system", "content": "You are a helpful assistant."}]
    multi_line_input = False

    print(blue(f"Start chatting with the {selected_model} model (type 'quit' to stop)! Type '{MULI_LINE_MODE_TEXT}' to switch input mode."))
    print(green("Tip: During the chat, you can switch between single-line and multi-line input modes."))
    print(green(f"     Type '{MULI_LINE_MODE_TEXT}' to toggle between these modes. In multi-line mode, type 'END' to send your message."))

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
                print(blue("\n\nSwitched to multi-line input mode. Type 'END' to send message."))
                continue
            elif message.lower() == "quit":
                break
        else:
            message_lines = []
            while True:
                line = sys.stdin.readline().rstrip('\n')
                if line == MULI_LINE_MODE_TEXT:
                    multi_line_input = False
                    print(blue("\n\nSwitched to single-line input mode."))
                    break
                elif line.lower() == "end":
                    print()
                    break
                message_lines.append(line)
            message = '\n'.join(message_lines)
            if not multi_line_input:
                continue
        
        print()

        # exit if no prompt is provided
        if len(message) == 0:
            raise KeyboardInterrupt

        messages.append({"role": "user", "content": message})

        try:
            response = openai.ChatCompletion.create(
                model=selected_model,
                messages=messages,
                stream=True
            )

            for chunk in response:
                chunk_message = chunk.choices[0].delta.get("content")
                if chunk_message:
                    last_line = chunk_message
                    sys.stdout.write(green(chunk_message))
                    sys.stdout.flush()

            chat_message = chunk.choices[0].delta.get("content", "")
            if chat_message:
                messages.append({"role": "assistant", "content": chat_message})
        except Exception as e:
            print(red(f"Error during chat: {e}"))
            break

def simple_date(epoch_time):
    date_time = datetime.datetime.fromtimestamp(epoch_time)
    formatted_date = date_time.strftime("%B %d, %Y")
    return formatted_date

def main():
    parser = argparse.ArgumentParser(description="Chat with an OpenAI GPT model.")
    parser.add_argument('-m', '--model', help='Model to use for chatting', required=False)

    args = parser.parse_args()

    openai_models = list_models()

    if args.model and any(model[0] == args.model for model in openai_models):
        selected_model = args.model
    else:
        print(yellow("Available OpenAI Models:"))
        max_length = max(len(model_id) for model_id, _ in openai_models)
        openai_models = sorted(openai_models, key=lambda x: x[1])
        for model_id, created in openai_models:
            formatted_model_id = model_id.ljust(max_length)
            print(yellow(f"   > {formatted_model_id}   {simple_date(created)}"))
        print()

        selected_model = input("Which model do you want to use? ")
        print()

    if selected_model not in [model[0] for model in openai_models]:
        print(red("Invalid model selected. Exiting."))
        return

    chatbot(selected_model)

def cli():
    try:
        main()
    except KeyboardInterrupt:
        print(red("\n\nExiting..."))

if __name__ == "__main__":
    cli()

