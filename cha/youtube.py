"""
March 7, 2024

The YouTube Scraper uses yt-dlp (https://github.com/yt-dlp/yt-dlp)
"""

import subprocess
import uuid
import time
import json
import os
import re

from groq import Groq
from cha import colors, config


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


def execute(cmd):
    proc = subprocess.Popen(
        cmd,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    output, error = proc.communicate()
    output = output.decode("utf-8")
    error = error.decode("utf-8")
    if proc.returncode != 0:
        print(colors.red(f"Failed to execute command {cmd} due to error: {error}"))
    return output.split("\n")


def rm_repeated_empty_strs(lst):
    return [v for i, v in enumerate(lst) if v != "" or lst[i - 1] != ""]


def parse_transcript(transcript_lines):
    transcript_dict = {}
    current_sentence = ""
    current_time = ""

    for line in transcript_lines:
        if "-->" in line:
            current_time = line.split(" --> ")[0]

            if current_sentence:
                transcript_dict[current_time] = current_sentence.strip()
                current_sentence = ""
        elif line.isdigit() or line == "":
            continue
        else:
            current_sentence += line + " "

    if current_time and current_sentence:
        transcript_dict[current_time] = current_sentence.strip()

    return transcript_dict


def valid_yt_link(link):
    if "www.youtube.com" not in link:
        return False
    if "//" not in link:
        return False
    if "v=" not in link:
        return False
    if "http" not in link:
        return False
    return True


def extract_yt_transcript(url):
    try:
        # NOTE: remove aditional metadata from URL
        url = url.split("&")[0]

        file_id = str(uuid.uuid4())
        filename = f"yt_sub_{int(time.time())}_{file_id}"

        cmd = config.build_youtube_scrape_cmd(url, filename)
        execute(cmd)

        root_dir = os.getcwd()
        output_file = ""
        for file in os.listdir(root_dir):
            if filename in file:
                output_file = os.path.join(root_dir, file)
                break

        content = parse_transcript(rm_repeated_empty_strs(read_file(output_file)))

        full_content = ""
        for key in content:
            full_content = full_content + " " + content[key]
        full_content = re.sub(r"\s+", " ", full_content.replace("[Music]", ""))

        if ".srt" in output_file and file_id in output_file:
            os.remove(output_file)
        else:
            print(
                colors.red(
                    f"\n\nfailed to delete file {output_file} from YouTube scrape\n\n"
                )
            )

        return full_content
    except Exception as e:
        print(colors.red(f"Error occurred with YouTube scraper: {e}"))
        return None


def download_youtube_mp3(link):
    filename = os.path.dirname(__file__) + "/yt_" + str(uuid.uuid4()) + ".mp3"
    cmd = f"yt-dlp --extract-audio --audio-format mp3 -o {filename} {link}"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    result = result.stdout
    return filename


def audio_to_text(filename):
    client = Groq()
    with open(filename, "rb") as file:
        transcription = client.audio.transcriptions.create(
            file=(filename, file.read()),
            model="whisper-large-v3",
            # prompt="Specify context or spelling",
            response_format="json",
            language="en",
            temperature=0.0,
        )
        return transcription.text


def extract_yt_auto_transcript(url):
    try:
        st1 = time.time()
        file = download_youtube_mp3(url)
        rt1 = time.time() - st1

        st2 = time.time()
        content = audio_to_text(file)
        rt2 = time.time() - st2

        st3 = time.time()
        os.remove(file)
        rt3 = time.time() - st3

        return {
            "content": content,
            "filename": file,
            "runtimes": {"yt_down_sec": rt1, "to_text_sec": rt2, "rm_file_sec": rt3},
        }
    except:
        return None


def main_yt_pointer(url):
    if not valid_yt_link(url):
        print(colors.red("Error: Invalid YouTube URL"))
        print(colors.red(f"Provided URL: {url}"))
        return None

    print(colors.yellow(f"\nYouTube URL detected:"))
    print(colors.yellow(f"> {url}"))

    # NOTE: only provide the ability to use the advance yt scarpper if they provided a GROQ API key
    if len(os.environ.get("GROQ_API_KEY", "")) > 0:
        user_prompt = "\nUse the slow but accurate scraper? (y/n): "
        user_input = input(colors.blue(user_prompt)).lower()
    else:
        user_input = ""

    try:
        if user_input in ["yes", "y"]:
            print(colors.yellow("\nUsing advanced yt audio scraper...\n"))
            output = extract_yt_auto_transcript(url)
            if output is None:
                raise Exception("Failed to perform advanced yt audio scrape")
            return output["content"]

        print(colors.yellow("\nUsing simple yt transcript scraper...\n"))
        output = extract_yt_transcript(url)
        if output is None:
            raise Exception("Failed to perform simple yt transcript scrape")
        return output
    except Exception as e:
        print(colors.red(f"\nError: {str(e)}"))
        return None
