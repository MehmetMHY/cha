from contextlib import redirect_stdout, redirect_stderr
import statistics
import subprocess
import datetime
import tempfile
import warnings
import base64
import uuid
import json
import copy
import math
import sys
import re
import os

from docx import Document
from mutagen import File
from PIL import Image
import pytesseract
import openpyxl
import chardet
import base64
import fitz

from requests.packages.urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from moviepy import VideoFileClip
import tiktoken
import requests

from cha import colors, utils, config, answer, loading


def extract_code_blocks(text, file_start_str=""):
    output = {"created": [], "errors": [], "total": 0}

    pattern = r"```([a-zA-Z0-9+\-#]*)\n(.*?)```"
    matches = re.findall(pattern, text, re.DOTALL)
    for lang, code in matches:
        output["total"] += 1
        filename = None
        try:
            lang = lang.strip().lower() if lang else None
            extension = config.FILETYPE_TO_EXTENSION.get(lang, ".txt")

            filename = (
                str(file_start_str) + str(uuid.uuid4()).replace("-", "")[:8] + extension
            )
            filename = os.path.join(os.getcwd(), filename)
            with open(filename, "w", encoding="utf-8") as f:
                f.write(code.strip())

            output["created"].append(filename)
        except Exception as e:
            output["errors"].append(e)
            if filename != None and os.path.exists(filename):
                os.remove(filename)

    return output


def is_o_model(model_name):
    return re.match(r"^o\d+", model_name) is not None


def count_tokens(text, model_name, fast_mode=False, language=None, rounding=1.1):
    try:
        if fast_mode == False:
            encoding = tiktoken.encoding_for_model(model_name)
            return len(encoding.encode(text))

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


def transcribe_file(file_path):
    # NOTE: the import is made here to reduce initial loading time for the rest of the application
    import whisper

    if os.path.exists(file_path) == False:
        raise Exception(f"Audio file {file_path} does not exist")

    if type(file_path) != str:
        raise Exception("Inputted file_path is NOT type string")

    # suppress user warnings from Whisper
    warnings.filterwarnings("ignore", category=UserWarning)

    model = whisper.load_model(config.DEFAULT_WHISPER_MODEL_NAME)
    result = model.transcribe(file_path)

    segments = result.get("segments", [])
    standardized_output = []
    for seg in segments:
        speaker = "?"
        start_time = seg.get("start", 0.0)
        end_time = seg.get("end", 0.0)
        text = seg.get("text", "")
        standardized_output.append(
            {"speaker": speaker, "start": start_time, "end": end_time, "text": text}
        )

    return {
        "standard": standardized_output,
        "raw": result,
        "platform": "local_whisper",
    }


def load_most_files(
    file_path, client, model_name=config.CHA_DEFAULT_IMAGE_MODEL, prompt=None
):
    file_ext = os.path.splitext(file_path)[1].lower()

    if file_ext in [".jpg", ".jpeg", ".png"]:
        traditional_method = pytesseract.image_to_string(Image.open(file_path))

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

        llm_method = response.choices[0].message.content

        return f"""
The LLM model "{model_name}" extracted the following from the image:

```
{llm_method}
```

The traditional, None-LLM method, extracted the following from the image:

```
{traditional_method}
```

Either methods are perfect, they both have their pros and cons. That is why,
both methods were utilized and their outputs were presented. So place your,
judgement based on both methods.
""".strip()

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

    elif file_ext in config.LOCAL_WHISPER_SUPPORTED_FORMATS:
        try:
            audio_data = str(File(file_path).pprint()).strip()
            content = transcribe_file(file_path=file_path)
            transcript = ""
            for entry in content.get("standard"):
                start = round(entry.get("start"), 2)
                end = round(entry.get("end"), 2)
                text = entry.get("text")
                transcript += f"[{start}-{end}] {text.strip()}\n"
            if transcript.endswith("\n"):
                transcript = transcript[:-1]
            return f"""
Audio File's Name:
```
{file_path}
```

MetaData:
```
{audio_data}
```

Transcript:
```
{transcript}
```
""".strip()
        except Exception as e:
            loading.print_message(
                colors.red(f"Failed to load audio file {file_path} due to {e}")
            )
            return None

    elif file_ext in config.SUPPORTED_VIDEO_FORMATS:
        content = extract_text_from_video(file_path)
        if type(content) == dict:
            return str(content.get("standard"))

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


def extract_audio_from_video(video_path):
    try:
        if not os.path.exists(video_path):
            return None

        audio_filepath = os.path.join(
            tempfile.gettempdir(), f"audio_{str(uuid.uuid4())}.mp3"
        )

        video = VideoFileClip(video_path)

        if video.audio is None:
            video.close()
            return None

        video.audio.write_audiofile(audio_filepath)
        video.close()

        if os.path.exists(audio_filepath):
            return audio_filepath
    except Exception:
        pass

    return None


def extract_text_from_video(video_path):
    result = None
    with open(os.devnull, "w") as fnull:
        with redirect_stdout(fnull), redirect_stderr(fnull):
            result = extract_audio_from_video(video_path)
    output = None
    if result != None and os.path.exists(result):
        output = transcribe_file(result)
        os.remove(result)
    return output
