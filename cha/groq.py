"""
## Install Depends

pip install groq

## Notes

Name the environment variable "GROQ_API_KEY"

## Sources

- https://console.groq.com/docs/speech-text
- https://console.groq.com/docs/models
"""

import subprocess
import time
import json
import uuid
import os

from groq import Groq


def execute(command):
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    return result.stdout


def download_youtube_mp3(link):
    filename = os.path.dirname(__file__) + "/yt_" + str(uuid.uuid4()) + ".mp3"
    cmd = f"yt-dlp --extract-audio --audio-format mp3 -o {filename} {link}"
    output = execute(cmd)
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


# main function calls
url = input("YouTube URL: ")
output = extract_yt_auto_transcript(url)
print(json.dumps(output, indent=4))
