import openai
import os
import sys
import argparse
import datetime
import subprocess
import requests
import json
import copy

import sseclient
import requests
from bs4 import BeautifulSoup

# hard coded config values
MULI_LINE_MODE_TEXT = "~!"

openai.api_key = os.getenv("OPENAI_API_KEY")

def red(text): return f"\033[91m{text}\033[0m"
def green(text): return f"\033[92m{text}\033[0m"
def yellow(text): return f"\033[93m{text}\033[0m"
def blue(text): return f"\033[94m{text}\033[0m"

DEFAULT_TOGETHER_PARAMS = {
    "model": None,
    "prompt": None,
    "max_tokens": 512,
    "temperature": 0.7,
    "top_p": 0.7,
    "top_k": 50,
    "repetition_penalty": 1,
    "stream_tokens": True
}

def execute(cmd):
    proc = subprocess.Popen(str(cmd), shell=True, stdout=subprocess.PIPE,)
    output = proc.communicate()[0].decode("utf-8")
    return output.split("\n")

def open_dashboard():
    url = "https://platform.openai.com/usage"
    cmd = f"open {url}"
    execute(cmd)
    return

# https://ollama.ai/
def ollama_running():
    url = 'http://127.0.0.1:11434/'
    try:
        response = requests.get(url, timeout=5)
        response = response.text
        if response != "Ollama is running":
            raise Exception("Ollama is not running!")
        return True
    except Exception as err:
        return False

def get_ollama_models():
    data = execute("ollama list")
    models = []
    for i in range(len(data)):
        if i == 0:
            continue
        tmp = data[i].split("\t")[0].replace(" ", "")
        if tmp != "":
            models.append(tmp)
    return models

def extract_type(table_name):
    try:
        return str(table_name).split(" ")[0].lower()
    except:
        return table_name

def scrape_and_format_tables(urls):
    formatted_data = []
    for url in urls:
        # fetch the webpage content
        response = requests.get(url)
        html_content = response.content

        # parse the HTML content
        soup = BeautifulSoup(html_content, 'html.parser')

        # find all tables in the HTML
        tables = soup.find_all('table')

        # extracting and formatting data from each table
        for table in tables:
            table_name = table.find_previous(class_='heading-text').text if table.find_previous(class_='heading-text') else "Unknown Type"
            rows = table.find_all('tr')[1:]  # skip the header row

            for row in rows:
                cols = row.find_all('td')
                cols_text = [ele.text.strip() for ele in cols]

                # ensure there are enough columns to unpack
                if len(cols_text) >= 3:
                    context_length = None
                    if len(cols_text) >= 4:
                        context_length = cols_text[3]

                    formatted_row = {
                        "organization": cols_text[0],
                        "model": cols_text[1],
                        "api_name": cols_text[2],
                        "context_length": context_length,
                        "type": extract_type(table_name)
                    }

                    formatted_data.append(formatted_row)

    return formatted_data

def get_together_ai_text_models():
    # current URL(s) as of 1-19-2024
    urls = [
        "https://docs.together.ai/docs/inference-models",
        "https://docs.together.ai/docs/inference-models-dedicated"
    ]

    formatted_tables = scrape_and_format_tables(urls)

    output = []
    for entry in formatted_tables:
        if entry["type"] != "chat":
            api_name = entry["api_name"]
            if api_name not in output:
                output.append(api_name)

    return list(set(output))

def list_models():
    try:
        response = openai.Model.list()
        if not response['data']:
            raise ValueError('No models available')
        openai_models = [(model['id'], model['created']) for model in response['data'] if "gpt" in model['id'] and "instruct" not in model['id']]
        ollama_models = get_ollama_models()
        together_ai_models = get_together_ai_text_models()
        return openai_models, ollama_models, together_ai_models
    except Exception as e:
        print(red(f"Error fetching models: {e}"))
        sys.exit(1)

def chatbot(selected_model, model_type):
    if model_type == "OpenAI":
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
    elif model_type == "TogetherAI":
        print(blue(f"Start chatting with the {selected_model} model (type 'quit' to stop)!"))
        print(green("Type your message and press enter to send."))
        print()

        last_line = ""
        while True:
            if last_line and not last_line.endswith('\n'):
                print()

            print("User: ", end="", flush=True)
            try:
                prompt = input()
            except:
                sys.exit(1)
            if prompt.lower() == 'quit':
                break

            payload = copy.deepcopy(DEFAULT_TOGETHER_PARAMS)
            payload["model"] = selected_model
            payload["prompt"] = prompt

            headers = {
                "Authorization": f"Bearer {os.getenv('TOGETHER_API_KEY')}",
            }

            try:
                response = requests.post("https://api.together.xyz/inference", json=payload, headers=headers, stream=True)
                response.raise_for_status()
                client = sseclient.SSEClient(response)
                print(green("AI: "), end="")
                for event in client.events():
                    if event.data == "[DONE]":
                        break
                    partial_result = json.loads(event.data)
                    token = partial_result["choices"][0]["text"]
                    last_line = token
                    print(token, end="", flush=True)
                print("\n")
            except requests.exceptions.HTTPError as e:
                print(red(f"HTTP error: {e}"))
            except requests.exceptions.RequestException as e:
                print(red(f"Error: {e}"))

def simple_date(epoch_time):
    date_time = datetime.datetime.fromtimestamp(epoch_time)
    formatted_date = date_time.strftime("%B %d, %Y")
    return formatted_date

def main():
    parser = argparse.ArgumentParser(description="Chat with an AI model.")
    parser.add_argument('-m', '--model', help='Model to use for chatting', required=False)
    parser.add_argument('-c', '--cost', action='store_true', help="Open the OpenAI cost dashboard")

    args = parser.parse_args()

    if args.cost:
        open_dashboard()
        sys.exit(0)

    openai_models, ollama_models, together_ai_models = list_models()

    selected_model = None
    model_type = None

    if args.model:
        if any(model[0] == args.model for model in openai_models):
            selected_model = args.model
            model_type = "OpenAI"
        elif args.model in ollama_models:
            selected_model = args.model
            model_type = "Ollama"
        elif args.model in together_ai_models:
            selected_model = args.model
            model_type = "TogetherAI"
        else:
            print(red("Invalid model selected. Exiting."))
            return
    else:
        print(yellow("Available Togther.AI Models:"))
        for model in together_ai_models:
            print(yellow(f"   > {model}"))
        print()

        print(yellow("Available OpenAI Models:"))
        max_length = max(len(model_id) for model_id, _ in openai_models)
        openai_models = sorted(openai_models, key=lambda x: x[1])
        for model_id, created in openai_models:
            formatted_model_id = model_id.ljust(max_length)
            print(yellow(f"   > {formatted_model_id}   {simple_date(created)}"))
        print()

        print(yellow("Available Ollama Models:"))
        for model in ollama_models:
            print(yellow(f"   > {model}"))
        print()

        selected_model = input("Which model do you want to use? ")
        print()

        # Determine the model type based on user input
        if any(model[0] == selected_model for model in openai_models):
            model_type = "OpenAI"
        elif selected_model in ollama_models:
            model_type = "Ollama"
        elif selected_model in together_ai_models:
            model_type = "TogetherAI"
        else:
            print(red("Invalid model selected. Exiting."))
            return

    if selected_model not in [model[0] for model in openai_models] and selected_model not in ollama_models and selected_model not in together_ai_models:
        print(red("Invalid model selected. Exiting."))
        return

    if selected_model in ollama_models and not ollama_running():
        print(red("Ollama is not running. Exiting."))
        return

    chatbot(selected_model, model_type)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(red("\n\nExiting..."))


