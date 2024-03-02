"""
March 2, 2024

This script is still in beta, run at your own risk!
"""

import subprocess
import json
import time
import os
import re

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

def read_json(path):
    with open(str(path)) as file:
        content = json.load(file)
    return content

def write_json(path, data):
    with open(str(path), "w") as file:
        json.dump(data, file, indent=4)

def create_file(path):
    file = open(str(path), "a+")
    file.close()

def execute(cmd):
    proc = subprocess.Popen(str(cmd), shell=True, stdout=subprocess.PIPE,)
    output = proc.communicate()[0].decode("utf-8")
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

# MAIN FUNCTION CALLS

url = "https://www.youtube.com/watch?v=-Am0vMW3fA0"

filename = f"yt_sub_{int(time.time())}_{url.split('=')[1]}"

# NOTE: make sure to install yt-dlp (https://github.com/yt-dlp/yt-dlp)
# NOTE: the command was from https://www.reddit.com/r/youtubedl/comments/15fcrmd/transcript_extract_from_youtube_videos_ytdlp/
cmd = f"yt-dlp --write-auto-sub --convert-subs=srt --skip-download {url} -o {filename}"
execute(cmd)

root_dir = os.path.dirname(os.path.abspath(__file__))
output_file = ""
for file in os.listdir(root_dir):
    if filename in file:
        output_file = os.path.join(root_dir, file)
        break

content = rm_repeated_empty_strs( read_file(output_file) )
content = parse_transcript(content)

full_content = ""
for key in content:
    full_content = full_content + " " + content[key]
full_content = full_content.replace("[Music]", "")
full_content = re.sub(r'\s+', ' ', full_content)

if ".srt" in output_file:
    os.remove(output_file)

print(full_content)

