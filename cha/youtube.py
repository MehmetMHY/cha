"""
March 7, 2024

The YouTube Scrapper uses yt-dlp (https://github.com/yt-dlp/yt-dlp)
"""

import subprocess
import uuid
import time
import json
import os
import re

from cha import colors


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
        if not valid_yt_link(url):
            raise Exception(f"URL {url} it NOT a valid YouTube url/link")
        
        # NOTE: remove aditional metadata from URL
        url = url.split("&")[0]

        file_id = str(uuid.uuid4())
        filename = f"yt_sub_{int(time.time())}_{file_id}"

        # NOTE: make sure to install yt-dlp (https://github.com/yt-dlp/yt-dlp)
        # NOTE: the command was from https://www.reddit.com/r/youtubedl/comments/15fcrmd/transcript_extract_from_youtube_videos_ytdlp/
        cmd = f"yt-dlp --write-auto-sub --convert-subs=srt --skip-download {url} -o {filename}"
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
        print(colors.red(f"Error occurred with YouTube scrapper: {e}"))
        return None
