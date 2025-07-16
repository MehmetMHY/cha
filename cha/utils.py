import statistics
import subprocess
import tempfile
import textwrap
import random
import base64
import uuid
import json
import copy
import math
import sys
import re
import os

from cha import colors, config


def run_fzf_ssh_safe(fzf_args, input_text, return_process=False):
    import shlex
    from collections import namedtuple

    output_tmp_file = tempfile.NamedTemporaryFile(
        mode="w", delete=False, encoding="utf-8"
    )
    output_tmp_file.close()  # we only need the name

    try:
        # quote each argument to make it safe for the shell
        safe_fzf_args = " ".join(shlex.quote(arg) for arg in fzf_args)

        # construct the full shell command with redirection.
        # fzf's selection (stdout) will go to the temp file.
        # its interactive ui (stderr) will go to the terminal.
        command = f"{safe_fzf_args} > {shlex.quote(output_tmp_file.name)}"

        # run the command, passing the list of items to fzf via stdin.
        # we do not capture stdout/stderr, so fzf can use the terminal.
        process = subprocess.run(
            command,
            shell=True,
            input=input_text,
            text=True,
            encoding="utf-8",
            check=False,
        )

        # read the selection from the temporary output file
        with open(output_tmp_file.name, "r", encoding="utf-8") as f:
            result = f.read().strip()

        # this part is for editor.py which needs the process result
        if return_process:
            ProcessResult = namedtuple("ProcessResult", ["returncode", "stdout"])
            return ProcessResult(returncode=process.returncode, stdout=result)
        else:
            # fzf returns 130 on esc, 1 on no match. we want to return none for both.
            if process.returncode != 0:
                return None
            return result

    finally:
        # clean up the temporary file
        os.unlink(output_tmp_file.name)


def number_of_urls(text):
    url_pattern = r"https?://(?:www\.)?\S+"
    urls = re.findall(url_pattern, text)
    return len(urls)


def get_json_serializable_globals(mod):
    def is_json_serializable(v):
        try:
            json.dumps(v)
            return True
        except (TypeError, OverflowError):
            return False

    return {
        k: v
        for k, v in vars(mod).items()
        if not (k.startswith("__") and k.endswith("__")) and is_json_serializable(v)
    }


def contains_date(s):
    # Month DD, YYYY (case-insensitive)
    month_date_pattern = r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}\b"
    # YYYY-MM-DD (ISO)
    iso_pattern = r"\b\d{4}-\d{1,2}-\d{1,2}\b"
    # MM-DD-YYYY and DD-MM-YYYY
    dash_pattern = r"\b\d{1,2}-\d{1,2}-\d{4}\b"
    patterns = [month_date_pattern, iso_pattern, dash_pattern]
    return any(re.search(p, s, re.IGNORECASE) for p in patterns)


def run_a_shell(command=None):
    try:
        current_dir = os.getcwd()

        # if command is provided, execute it directly
        if command:
            # check if command is blocked (very dangerous commands only)
            cmd_parts = command.split()
            if cmd_parts and cmd_parts[0] in config.BLOCKED_SHELL_COMMANDS:
                print(
                    colors.red(
                        f"Command '{cmd_parts[0]}' is blocked for security reasons"
                    )
                )
                return

            # execute the command with proper interrupt handling
            try:
                # use popen for better control over process
                process = subprocess.Popen(
                    command,
                    shell=True,
                    cwd=current_dir,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )

                try:
                    # wait for process with timeout
                    stdout, stderr = process.communicate(timeout=30)

                    # print output in white (no colors)
                    if stdout:
                        print(stdout.rstrip())
                    if stderr:
                        print(stderr.rstrip())

                    if process.returncode != 0:
                        print(
                            colors.red(f"Command exited with code {process.returncode}")
                        )

                except subprocess.TimeoutExpired:
                    # kill the process if it times out
                    process.kill()
                    process.wait()
                    print(colors.red("Command timed out after 30 seconds"))

            except KeyboardInterrupt:
                # handle ctrl+c gracefully - kill the process but don't exit cha
                try:
                    process.kill()
                    process.wait()
                except:
                    pass
                print(colors.yellow("Command interrupted by user"))
                return
            except Exception as e:
                print(colors.red(f"Error executing command: {e}"))
            return

        # Original interactive shell logic
        current_shell = os.environ.get("SHELL")
        chosen_name = None

        # use fish shell by default
        try:
            result = subprocess.run(
                ["which", "fish"], capture_output=True, text=True, check=True
            )
            fish_shell = result.stdout.strip()
            if current_shell != fish_shell:
                chosen_name = fish_shell
        except subprocess.CalledProcessError:
            pass

        # use random but already installed shell if the fish shell is not installed
        if chosen_name == None:
            shell_dir = "/etc/shells"
            with open(shell_dir) as f:
                shells = [line.strip() for line in f if line.startswith("/")]
            shells = [x for x in list(set(shells)) if x != current_shell]
            shells.sort()
            if len(shells) > 0:
                chosen_name = random.choice(shells)

        if chosen_name == None:
            raise Exception(f"Zero shells found")

        columns, _ = os.get_terminal_size()
        padding_length = (columns - len(chosen_name) - 2) // 2
        left_padding = "=" * padding_length
        right_padding = "=" * (columns - len(left_padding) - len(chosen_name) - 2)
        line_text = f"{left_padding}[{chosen_name}]{right_padding}"

        print(colors.green(line_text))
        subprocess.run(chosen_name, cwd=os.getcwd())
        print(colors.green(line_text))

    except Exception as e:
        print(colors.red(f"Error running shell: {e}"))

    return


def export_file_logic(text_content, force_single_file=False):
    try:
        extracted = extract_code_blocks(
            text=text_content,
            file_start_str="export_",
            force_single_file=force_single_file,
        )

        if extracted["total"] == 0:
            print(colors.yellow("No blocks found for exporting"))

        if len(extracted["errors"]) > 0:
            print(
                colors.red(
                    f"Failed to export {len(extracted['errors'])} blocks to files: {extracted}"
                )
            )

        if len(extracted["created"]) > 0:
            for f in extracted["created"]:
                print(colors.green(f"- {f}"))

    except Exception as e:
        print(colors.red(f"Failed to export code block(s) due to {e}"))

    return


def extract_code_blocks(text, file_start_str="", force_single_file=False):
    output = {"created": [], "errors": [], "total": 0, "brute_method": False}

    # improved regex pattern to handle more variations
    pattern = r"```\s*([a-zA-Z0-9+\-#./]*)\s*\n(.*?)```"
    matches = []
    if not force_single_file:
        matches = re.findall(pattern, text, re.DOTALL | re.MULTILINE)

    # if no code blocks were found, save the entire text as a .txt file
    if not matches:
        output["total"] += 1
        output["brute_method"] = False
        if force_single_file == False:
            output["brute_method"] = True
        filename = str(file_start_str) + str(uuid.uuid4()).replace("-", "")[:8] + ".txt"
        filename = os.path.join(os.getcwd(), filename)
        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(text.strip())
            output["created"].append(filename)
        except Exception as e:
            output["errors"].append(e)
        return output

    for lang, code in matches:
        output["total"] += 1
        filename = None
        try:
            lang = lang.strip().lower() if lang else None

            # handle empty language specifier
            if not lang:
                lang = "txt"

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
            if filename is not None and os.path.exists(filename):
                os.remove(filename)

    return output


def is_slow_model(model_name):
    if config.BY_PASS_SLOW_MODEL_DETECTION == True:
        return False
    else:
        return re.match(r"^o\d+", model_name) is not None


def count_tokens(text, model_name, fast_mode=False, language=None, rounding=1.25):
    try:
        if fast_mode == False:
            import tiktoken

            try:
                encoding = tiktoken.encoding_for_model(model_name)
                return len(encoding.encode(text))
            except:
                new_model_name = "o1" if model_name.startswith("o") else "gpt-4o"
                encoding = tiktoken.encoding_for_model(new_model_name)
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
    from requests.packages.urllib3.util.retry import Retry
    from requests.adapters import HTTPAdapter
    import requests

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


def safe_input(message=""):
    try:
        return input(message)
    except (KeyboardInterrupt, EOFError):
        print()
        sys.exit(0)


def write_json(path, data):
    with open(str(path), "w") as file:
        json.dump(data, file, indent=4)


def open_file_in_editor(file_path):
    """opens the given file path in a preferred terminal editor."""
    terminals = copy.deepcopy(config.SUPPORTED_TERMINAL_IDES)
    if config.PREFERRED_TERMINAL_IDE:
        terminals.insert(0, config.PREFERRED_TERMINAL_IDE)

    for editor in terminals:
        try:
            # check if the editor is installed by checking its version
            subprocess.run(
                [editor, "--version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
            )
            # open the editor with the file
            subprocess.run([editor, file_path])
            return True
        except (FileNotFoundError, subprocess.CalledProcessError):
            continue
    return False


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
    try:
        os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
        # NOTE: the import is made here to reduce initial loading time for the rest of the application
        from faster_whisper import WhisperModel

        if os.path.exists(file_path) == False:
            raise Exception(f"Audio file {file_path} does not exist")

        if type(file_path) != str:
            raise Exception("Inputted file_path is NOT type string")

        model = WhisperModel(
            config.DEFAULT_WHISPER_MODEL_NAME, device="cpu", compute_type="int8"
        )

        segments, info = model.transcribe(file_path, beam_size=5)
        transcript = ""
        for segment in segments:
            line = "[%.3fs -> %.3fs] %s" % (segment.start, segment.end, segment.text)
            transcript = transcript + line + "\n"

        return transcript
    except Exception as e:
        return {"error": e}


def load_most_files(
    file_path, client, model_name=config.CHA_DEFAULT_IMAGE_MODEL, prompt=None
):
    file_ext = os.path.splitext(file_path)[1].lower()

    if file_ext in config.SUPPORTED_IMG_FORMATS:
        from PIL import Image
        import pytesseract

        traditional_method = pytesseract.image_to_string(Image.open(file_path))

        with open(file_path, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode("utf-8")

        try:
            chat_history = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            },
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
        except:
            llm_method = None

        return rls(
            f"""
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
            """
        )

    elif file_ext in config.SUPPORTED_PDF_FORMATS:
        import fitz

        document = fitz.open(file_path)
        text = ""
        for page_num in range(document.page_count):
            page = document[page_num]
            text += page.get_text()
        document.close()
        return text

    elif file_ext in config.SUPPORTED_DOC_FORMATS:
        from docx import Document

        doc = Document(file_path)
        return "\n".join([paragraph.text for paragraph in doc.paragraphs])

    elif file_ext in config.SUPPORTED_SPREAD_SHEET_FORMATS:
        import openpyxl

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

    elif file_ext in config.SUPPORTED_AUDIO_FORMATS:
        from mutagen import File

        audio_data = str(File(file_path).pprint()).strip()
        transcript = transcribe_file(file_path=file_path)
        if type(transcript) == dict:
            print(
                colors.red(f"Failed to load audio file {file_path} due to {transcript}")
            )
            return None
        if transcript.endswith("\n"):
            transcript = transcript[:-1]
        return rls(
            f"""
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
            """
        )

    elif file_ext in config.SUPPORTED_VIDEO_FORMATS:
        content = extract_text_from_video(file_path)
        if type(content) == dict:
            return str(content.get("standard"))

    else:
        import chardet

        # get exact file encoding
        with open(file_path, "rb") as file:
            raw_data = file.read()
            result = chardet.detect(raw_data)
            encoding = result["encoding"]

        with open(file_path, "r", encoding=encoding, errors="replace") as file:
            return file.read()


def act_as_ocr(client, filepath, prompt=None):
    default_prompt = rls(
        f"""
        Analyze the provided image and perform the following tasks:
        1. Extract all visible text accurately, including any embedded or obscured text.
        2. Interpret the contextual meaning of the image by examining visual elements, symbols, and any implied narratives or themes.
        3. Identify relationships between the text and visual components, noting any cultural, historical, or emotional subtleties.
        Provide a comprehensive report combining literal text extraction with nuanced interpretations of the image's symbolic and contextual messages.
        Also note, that the file name is named "{filepath}" which might or might not provide more context of the image.
        """
    )
    try:
        current_prompt = default_prompt
        if type(prompt) == None:
            current_prompt = default_prompt
        if "/" not in filepath:
            filepath = "./" + filepath
        content = load_most_files(
            file_path=filepath, client=client, prompt=current_prompt
        )
        return str(content)
    except Exception as e:
        return None


def extract_audio_from_video(video_path):
    try:
        from moviepy import VideoFileClip

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
    from contextlib import redirect_stdout, redirect_stderr

    result = None
    with open(os.devnull, "w") as fnull:
        with redirect_stdout(fnull), redirect_stderr(fnull):
            result = extract_audio_from_video(video_path)
    output = None
    if result != None and os.path.exists(result):
        output = transcribe_file(result)
        os.remove(result)
    return output


def normalize_whitespace(text: str, tab_size: int = 4) -> str:
    """
    Replaces various (often-unnoticed) whitespace characters with standard spaces,
    collapses consecutive spaces in the 'middle' of the text, and preserves all
    leading and trailing spaces exactly as they appear (after converting any
    special characters to spaces but not collapsing them).
    """

    # mapping of special whitespace characters to their replacements
    whitespace_map = {
        "\t": " " * tab_size,  # replace tabs with a specified number of spaces
        "\n": " ",  # replace newlines with single spaces
        "\r": " ",  # replace carriage returns with single spaces
        "\u00a0": " ",  # non-breaking space
        "\u2000": " ",  # en/em and other Unicode spaces
        "\u2001": " ",
        "\u2002": " ",
        "\u2003": " ",
        "\u2004": " ",
        "\u2005": " ",
        "\u2006": " ",
        "\u2007": " ",
        "\u2008": " ",
        "\u2009": " ",
        "\u200a": " ",
    }

    # extract leading and trailing whitespace
    leading_match = re.match(r"^\s+", text)
    leading = leading_match.group() if leading_match else ""
    trailing_match = re.search(r"\s+$", text)
    trailing = trailing_match.group() if trailing_match else ""

    # NOTE: the middle portion is whatever is left after removing detected leading/trailing
    middle = text[len(leading) : len(text) - len(trailing)]

    # replace special whitespace in each portion
    for char, replacement in whitespace_map.items():
        leading = leading.replace(char, replacement)
        trailing = trailing.replace(char, replacement)
        middle = middle.replace(char, replacement)

    # collapse consecutive spaces only in the middle portion
    middle = re.sub(r"\s+", " ", middle)

    # reconstruct the string with original leading and trailing space counts
    return leading + middle + trailing


def format_path_for_fzf(path):
    """
    format a file/directory path for better fzf display.
    returns: filename/:full_path for directories, filename:full_path for files
    """
    if os.path.isdir(path):
        dirname = os.path.basename(path) or os.path.basename(os.path.dirname(path))
        return f"{dirname}/:{path}"
    else:
        filename = os.path.basename(path)
        return f"{filename}:{path}"


def extract_path_from_fzf_format(formatted_line):
    """
    extract the actual path from a formatted fzf line.
    input: "filename/:full_path" or "filename:full_path"
    returns: full_path
    """
    if ":/" in formatted_line:
        # handle directory format "dirname/:full_path"
        return "/" + formatted_line.split(":/", 1)[1]
    elif ":" in formatted_line:
        # handle file format "filename:full_path"
        path_part = formatted_line.split(":", 1)[1]
        # if it doesn't start with /, add it back
        if not path_part.startswith("/"):
            path_part = "/" + path_part
        return path_part
    return formatted_line  # fallback if format is unexpected


def format_paths_for_fzf(paths):
    """
    format a list of paths for fzf display.
    returns: (formatted_paths_list, path_mapping_dict)
    """
    formatted_paths = []
    path_mapping = {}

    for path in paths:
        formatted = format_path_for_fzf(path)
        formatted_paths.append(formatted)
        path_mapping[formatted] = path

    return formatted_paths, path_mapping


def extract_paths_from_fzf_selection(selected_lines, path_mapping=None):
    """
    extract actual paths from fzf selection output.
    """
    if not selected_lines:
        return []

    if isinstance(selected_lines, str):
        selected_lines = selected_lines.strip().split("\n")

    paths = []
    for line in selected_lines:
        line = line.strip()
        if not line:
            continue

        if path_mapping and line in path_mapping:
            paths.append(path_mapping[line])
        else:
            paths.append(extract_path_from_fzf_format(line))

    return paths


def rls(text: str, fast_mode: bool = False) -> str:
    if fast_mode:
        return textwrap.dedent(text)

    lines = text.split("\n")

    lc = 0
    for line in lines:
        line = normalize_whitespace(line)

        match = re.match(r"^\s*", line)
        c = len(match.group()) if match else 0

        if (lc > c and c > 0) or (lc == 0 and c > lc):
            lc = c

    if lc == 0:
        return text

    output = ""
    for line in lines:
        if len(line) >= lc:
            output = output + line[lc:] + "\n"
        else:
            output += "\n"

    return output.strip()
