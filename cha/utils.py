import subprocess
import datetime
import tempfile
import base64
import uuid
import json
import sys
import re
import os

import tiktoken
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

from cha import colors, utils, config, answer


def is_o_model(model_name):
    return re.match(r"^o\d+-", model_name) is not None


def count_tokens(text, model_name):
    try:
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
        # NOTE: this returns a requests OBJECT not a dict or string!
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
    for editor in config.SUPPORTED_TERMINAL_IDES:
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


def msg_content_load():
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
            file_pick = input(colors.yellow(f"File ID (1-{len(files)}): "))
            file_path = files[int(file_pick) - 1]
            break
        except KeyboardInterrupt:
            return None
        except EOFError:
            return None
        except:
            pass

    with open(file_path, "r") as file:
        content = file.read()

    prompt = input(colors.yellow("Additional Prompt: "))

    output = content
    if len(prompt) > 0:
        output = f"""
PROMPT: {prompt}
CONTENT:
``````````
{content}
``````````
"""

    return output


def run_answer_search(client, user_input_mode=True):
    try:
        utils.check_env_variable(
            "BRAVE_API_KEY", "https://api.search.brave.com/app/dashboard"
        )
        return answer.answer_search(client=client, user_input_mode=user_input_mode)
    except (KeyboardInterrupt, EOFError, SystemExit):
        return None
