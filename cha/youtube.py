import concurrent.futures
import subprocess
import json
import re
import uuid
import os

from youtube_transcript_api import YouTubeTranscriptApi
from cha import colors, utils


def clean_subtitle_text(input_text):
    try:
        # remove empty lines
        lines = input_text.splitlines()
        non_empty_lines = filter(lambda x: x.strip(), lines)

        # filter out lines that contain only numbers
        filtered_lines = filter(
            lambda x: not re.match(r"^[0-9]+$", x.strip()), non_empty_lines
        )

        # filter out timing lines
        filtered_lines = filter(
            lambda x: not re.match(r"^\d{2}:\d{2}:\d{2}", x.strip()), filtered_lines
        )

        # filter out lines containing "-->"
        filtered_lines = filter(lambda x: "-->" not in x, filtered_lines)

        # remove HTML tags
        lines_without_html = map(lambda x: re.sub(r"<[^>]*>", "", x), filtered_lines)

        # join text and fix spacing
        result = " ".join(lines_without_html)
        result = re.sub(r"\s+", " ", result).strip()

        return result
    except Exception as e:
        return None


def generate_command(url, lang="en"):
    # https://www.reddit.com/r/youtubedl/comments/15fcrmd/transcript_extract_from_youtube_videos_ytdlp/
    root_cmd = "yt-dlp --skip-download --write-subs --write-auto-subs"
    video_id = url.split("?")[1].split("&")[0].replace("v=", "")
    filename = f"cha_yt_{video_id}_{uuid.uuid4()}.srt"
    filepath = os.path.join(os.getcwd(), filename)
    cmd = f'{root_cmd} --sub-lang {lang} --sub-format ttml --convert-subs srt --output "{filepath}" "{url}"'
    return cmd, filepath, filename


def yt_dlp_youtube_transcript_extractor(url, lang="en"):
    try:
        # generate command and filepath
        cmd, filepath, _ = generate_command(url, lang)

        # expected subtitle file path
        subtitle_path = f"{filepath}.{lang}.srt"

        # run yt-dlp command and capture output
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

        if result.returncode != 0:
            raise Exception(f"yt-dlp command failed: {result.stderr}")

        # check if subtitle file exists
        if not os.path.exists(subtitle_path):
            raise Exception(f"no subtitles found for language: {lang}")

        # load and process subtitle content
        content = utils.read_file(subtitle_path)
        content = "\n".join(content)

        processed_content = clean_subtitle_text(content)

        # clean up the subtitle file
        try:
            os.remove(subtitle_path)
        except OSError:
            print(colors.red(f"failed to delete tmp file {subtitle_path}"))
            pass

        return processed_content

    except Exception as e:
        print(colors.red(f"yt-dlp scraper failed: {e}"))
        return None


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
    # https://github.com/yt-dlp/yt-dlp
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
    output = ""
    try:
        video_id = url.replace(" ", "").split("v=")[1]

        # https://github.com/jdepoix/youtube-transcript-api
        content = YouTubeTranscriptApi.get_transcript(video_id)

        for line in content:
            output = output + line["text"] + " "
    except Exception as e:
        # yt-dlp scraper isn't as good as youtube_transcript_api, but it's better than nothing
        print(colors.yellow(f"switching from API scraper to yt-dlp-based scraper"))
        output = yt_dlp_youtube_transcript_extractor(url, "en")

    return output


def youtube_scraper(url):
    with concurrent.futures.ThreadPoolExecutor() as executor:
        get_meta_data = executor.submit(video_metadata, url)
        get_transcript = executor.submit(video_transcript, url)

        meta_data = get_meta_data.result()
        transcript = get_transcript.result()

        meta_data["transcript"] = transcript

        return meta_data
