from datetime import datetime as dt, timezone
import statistics
import subprocess
import datetime
import tempfile
import base64
import uuid
import json
import copy
import math
import sys
import re
import os

from docx import Document
import openpyxl
import chardet
import base64
import fitz

from requests.packages.urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
import tiktoken
import requests

from cha import colors, utils, config, answer, loading


def is_o_model(model_name):
    return re.match(r"^o\d+", model_name) is not None


def fast_estimate_tokens(text, language=None, rounding=1.15):
    word_count = len(text.split())

    # https://gptforwork.com/guides/openai-gpt3-tokens
    token_multiplier = {
        "english": 1.3,
        "french": 2.0,
        "german": 2.1,
        "spanish": 2.1,
        "chinese": 2.5,
        "russian": 3.3,
        "vietnamese": 3.3,
        "arabic": 4.0,
        "hindi": 6.4,
    }

    if language is None or str(language.lower()) not in token_multiplier:
        tokens = word_count * statistics.median(token_multiplier.values())
    else:
        tokens = word_count * token_multiplier[language.lower()]

    return math.floor(tokens * rounding)


def count_tokens(text, model_name, fast_mode=False):
    try:
        if fast_mode:
            return fast_estimate_tokens(text=text)
        else:
            encoding = tiktoken.encoding_for_model(model_name)
            return len(encoding.encode(text))
    except:
        return None


def get_request(
    url,
    timeout=config.REQUEST_DEFAULT_TIMEOUT_SECONDS,
    retry_count=config.REQUEST_DEFAULT_RETRY_COUNT,
    headers=config.REQUEST_DEFAULT_HEADERS,
    debug_mode=False,
):
    retries = Retry(
        total=retry_count,
        backoff_factor=config.REQUEST_BACKOFF_FACTOR,
        status_forcelist=list(range(400, 600)),
    )

    session = requests.Session()
    session.mount("http://", HTTPAdapter(max_retries=retries))
    session.mount("https://", HTTPAdapter(max_retries=retries))

    try:
        response = session.get(url, timeout=timeout, headers=headers)
        response.raise_for_status()
        # NOTE: this returns a request's OBJECT not a dict or string!
        return response
    except requests.exceptions.RequestException as e:
        if debug_mode:
            print(colors.red(f"Failed to make GET request for {url} due to {e}"))
        return None


def check_env_variable(env_var_name, docs_url):
    if env_var_name not in os.environ:
        print(
            f"Environment variable '{env_var_name}' not found!\n\n"
            f"Please set your API key as an environment variable using:\n\n"
            f"  export {env_var_name}='your_api_key_here'\n\n"
            f"Obtain your API key here: {docs_url}"
        )
        sys.exit(1)


def safe_input(message=""):
    try:
        return input(message)
    except (KeyboardInterrupt, EOFError):
        print()
        sys.exit(0)


def generate_short_uuid():
    uuid_val = uuid.uuid4()
    uuid_bytes = uuid_val.bytes
    short_uuid = base64.urlsafe_b64encode(uuid_bytes).rstrip(b"=").decode("utf-8")
    return str(short_uuid)


def read_json(path):
    with open(str(path)) as file:
        content = json.load(file)
    return content


def write_json(path, data):
    with open(str(path), "w") as file:
        json.dump(data, file, indent=4)


def read_file(path):
    with open(str(path)) as file:
        content = file.readlines()
    content = [i.strip() for i in content]
    return content


def write_file(path, data):
    file = open(str(path), "w")
    for line in data:
        file.write(str(line) + "\n")
    file.close()


def simple_date(epoch_time):
    date_time = datetime.datetime.fromtimestamp(epoch_time)
    formatted_date = date_time.strftime("%B %d, %Y")
    return formatted_date


def check_terminal_editors_and_edit():
    terminals = copy.deepcopy(config.SUPPORTED_TERMINAL_IDES)
    if config.PREFERRED_TERMINAL_IDE != None:
        terminals.insert(0, config.PREFERRED_TERMINAL_IDE)

    for editor in terminals:
        try:
            # check if the editor is installed
            subprocess.run(
                [editor, "--version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
            )

            # create a temporary file
            with tempfile.NamedTemporaryFile(mode="w+", delete=False) as tmpfile:
                tmpfile_name = tmpfile.name

            # open the chosen editor with the temporary file
            subprocess.run([editor, tmpfile_name])

            # read the content from the temporary file
            with open(tmpfile_name, "r") as file:
                content = file.read()

            # attempt to delete the temporary file
            try:
                os.remove(tmpfile_name)
            except OSError:
                pass

            return content

        except (FileNotFoundError, subprocess.CalledProcessError):
            continue

    return None


def load_most_files(
    file_path, client, model_name=config.CHA_DEFAULT_IMAGE_MODEL, prompt=None
):
    file_ext = os.path.splitext(file_path)[1].lower()

    if file_ext in [".jpg", ".jpeg", ".png"]:
        with open(file_path, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode("utf-8")

        chat_history = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                    }
                ],
            }
        ]

        if type(prompt) == str:
            chat_history.append({"role": "user", "content": prompt})

        # NOTE: client in this case is an OpenAI client from OpenAI's Python SDK
        response = client.chat.completions.create(
            model=model_name, messages=chat_history
        )

        return response.choices[0].message.content

    elif file_ext == ".pdf":
        document = fitz.open(file_path)
        text = ""
        for page_num in range(document.page_count):
            page = document[page_num]
            text += page.get_text()
        document.close()
        return text

    elif file_ext in [".doc", ".docx"]:
        doc = Document(file_path)
        return "\n".join([paragraph.text for paragraph in doc.paragraphs])

    elif file_ext in [".xls", ".xlsx"]:
        workbook = openpyxl.load_workbook(file_path, data_only=True)
        text = ""
        for sheet in workbook:
            text += f"Sheet: {sheet.title}\n"
            consecutive_empty_rows = 0
            for row in sheet.iter_rows(values_only=True):
                formatted_row = "\t".join(
                    [str(cell).strip() if cell is not None else "" for cell in row]
                )
                # check if the row is empty (only contains tabs)
                if all(cell == "" for cell in formatted_row.split("\t")):
                    consecutive_empty_rows += 1
                else:
                    if consecutive_empty_rows > 0:
                        # add only one empty line if there were consecutive empty rows
                        text += "\t\n"
                        consecutive_empty_rows = 0
                    text += formatted_row + "\n"
            # reset counter at the end of the sheet, if it ended with empty rows
            if consecutive_empty_rows > 0:
                text += "\t\n"
        text = text.strip()
        return text

    else:
        # get exact file encoding
        with open(file_path, "rb") as file:
            raw_data = file.read()
            result = chardet.detect(raw_data)
            encoding = result["encoding"]

        with open(file_path, "r", encoding=encoding, errors="replace") as file:
            return file.read()


def msg_content_load(client):
    files = [
        f for f in os.listdir() if os.path.isfile(f) and f not in config.FILES_TO_IGNORE
    ]

    if len(files) == 0:
        print(colors.red(f"No files found in the current directory"), end="")
        return None

    print(colors.yellow(f"Current Directory:"), os.getcwd())
    print(colors.yellow("File(s):"))
    for i in range(len(files)):
        print(f"   {i+1}) {files[i]}")

    while True:
        try:
            file_pick = input(colors.yellow(f"File ID(s) (e.g. 1,2,3): "))
            file_indices = [
                int(x.strip()) - 1 for x in file_pick.replace(" ", "").split(",")
            ]
            if all(0 <= idx < len(files) for idx in file_indices):
                file_paths = [files[idx] for idx in file_indices]
                break
        except KeyboardInterrupt:
            return None
        except EOFError:
            return None
        except ValueError:
            pass
        print(colors.red("Invalid input, please try again."))

    prompt = input(colors.yellow("Additional Prompt: "))

    contents = []
    try:
        for file_path in file_paths:
            loading.start_loading(f"Loading {file_path}", "rectangles")
            content = load_most_files(
                client=client,
                file_path=file_path,
                model_name=config.CHA_DEFAULT_IMAGE_MODEL,
                prompt=prompt,
            )
            contents.append((file_path, content))
    except Exception as e:
        raise Exception(f"Failed to load files: {e}")
    finally:
        loading.stop_loading()

    output = "\n".join(
        f"CONTENT FOR {file_path}:\n``````````\n{content}\n``````````\n"
        for file_path, content in contents
    )

    if len(prompt) > 0:
        output = f"""
PROMPT: {prompt}
{output}
"""

    return output


def run_answer_search(client, prompt=None, user_input_mode=True):
    try:
        utils.check_env_variable("OPENAI_API_KEY", config.OPENAI_DOCS_LINK)
        return answer.answer_search(
            client=client, prompt=prompt, user_input_mode=user_input_mode
        )
    except (KeyboardInterrupt, EOFError, SystemExit):
        return None


def run_fast_search(message):
    original_message = str(message)

    try:
        default_print_browsing = True
        default_time_limit = False
        default_max_result = None
        if message.startswith(config.BROWSE_MODE_TEXT) and len(message) > (
            len(str(config.BROWSE_MODE_TEXT)) + 1 + 3
        ):
            default_print_browsing = False
            default_time_limit = None
            default_max_result = 3
        else:
            message = None

        message = answer.manual_search_engine(
            search_input=message,
            max_results=default_max_result,
            timelimit=default_time_limit,
            print_processes=default_print_browsing,
        )

        return f"""
For your answer, understand that today's date is: {dt.now(timezone.utc)}

The user made the following search engine query to DuckDuckGo's search engine:
```
{message["search_input"]}
```

The user made the search with the following parameters:
- max_results (max number of search results): {message["max_results"]}
- timelimit (filter search results by recency, allowing users to see only results from specific periods like in the past day, week, month, year or all time (none)): {message["timelimit"]}

The result is set to "English" by default and SafeSearch is disabled by default; these parameters are hard set and the user can not change that

Knowing all of this, the search was made and the content from each search result was quickly scraped and the following results were found:
```json
{message["results"]}
```

Use this as context for the user's future questions/prompts and answer the user's original question/prompt:
```
{original_message}
```
"""
    except (KeyboardInterrupt, EOFError, SystemExit):
        return None


def act_as_ocr(client, filepath, prompt=None):
    default_prompt = f"""
Analyze the provided image and perform the following tasks:
1. Extract all visible text accurately, including any embedded or obscured text.
2. Interpret the contextual meaning of the image by examining visual elements, symbols, and any implied narratives or themes.
3. Identify relationships between the text and visual components, noting any cultural, historical, or emotional subtleties.
Provide a comprehensive report combining literal text extraction with nuanced interpretations of the image's symbolic and contextual messages.
Also note, that the file name is named "{filepath}" which might or might not provide more context of the image.
"""
    try:
        current_prompt = default_prompt
        if type(prompt) == None:
            current_prompt = default_prompt
        if "/" not in filepath:
            filepath = "./" + filepath
        content = utils.load_most_files(
            file_path=filepath, client=client, prompt=current_prompt
        )
        return str(content)
    except Exception as e:
        return None
