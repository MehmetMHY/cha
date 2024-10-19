"""
October 15, 2024

This YouTube scraper uses the following tools
- yt-dlp: https://github.com/yt-dlp/yt-dlp
- youtube-transcript-api: https://github.com/jdepoix/youtube-transcript-api
"""

import concurrent.futures
import subprocess
import json
import re

from youtube_transcript_api import YouTubeTranscriptApi


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


def video_metadata(url):
    cmd = f"yt-dlp -j {url}"

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
        return {}

    content = json.loads(output)

    return {
        "title": content.get("title"),
        "description": re.sub(
            r"https?://\S+|www\.\S+", "", content.get("description", "")
        ),
        "duration": content.get("duration"),
        "view_count": content.get("view_count"),
        "like_count": content.get("like_count"),
        "channel": content.get("channel"),
        "channel_follower_count": content.get("channel_follower_count"),
        "uploader": content.get("uploader"),
        "upload_date": content.get("upload_date"),
        "epoch": content.get("epoch"),
        "fulltitle": content.get("fulltitle"),
    }


def video_transcript(url):
    video_id = url.replace(" ", "").split("v=")[1]
    content = YouTubeTranscriptApi.get_transcript(video_id)

    output = ""
    for line in content:
        output = output + line["text"] + " "

    return output


def youtube_scraper(url):
    with concurrent.futures.ThreadPoolExecutor() as executor:
        get_meta_data = executor.submit(video_metadata, url)
        get_transcript = executor.submit(video_transcript, url)

        meta_data = get_meta_data.result()
        transcript = get_transcript.result()

        meta_data["transcript"] = transcript

        return meta_data
