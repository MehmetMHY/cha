import concurrent.futures
import subprocess
import tempfile
import string
import json
import re
import os

import fitz  # PyMuPDF
from bs4 import BeautifulSoup
from youtube_transcript_api import YouTubeTranscriptApi
from cha import colors, utils, loading


def clean_yt_dlp_transcript(input_text):
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


def yt_dlp_transcript_extractor(url, lang="en"):
    try:
        # create a temporary file for the subtitle
        with tempfile.NamedTemporaryFile(delete=False, suffix=".srt") as tmp_file:
            base_filepath = tmp_file.name
            subtitle_path = f"{base_filepath}.{lang}.srt"

        # https://www.reddit.com/r/youtubedl/comments/15fcrmd/transcript_extract_from_youtube_videos_ytdlp/
        root_cmd = "yt-dlp --skip-download --write-subs --write-auto-subs"
        cmd = f'{root_cmd} --sub-lang {lang} --sub-format ttml --convert-subs srt --output "{base_filepath}" "{url}"'

        # run yt-dlp command and capture output
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

        if result.returncode != 0:
            raise Exception(f"yt-dlp command failed: {result.stderr}")

        # check if subtitle file exists
        if not os.path.exists(subtitle_path):
            raise Exception(f"no subtitles found for language: {lang}")

        # load and process subtitle content
        with open(subtitle_path, "r", encoding="utf-8") as file:
            content = file.read()

        processed_content = clean_yt_dlp_transcript(content)

        # clean up temporary files
        try:
            os.remove(base_filepath)
            os.remove(subtitle_path)
        except OSError as e:
            loading.print_message(colors.red(f"failed to delete temporary files: {e}"))

        return processed_content

    except Exception as e:
        # clean up temporary files in case of error
        try:
            if "base_filepath" in locals():
                os.remove(base_filepath)
            if "subtitle_path" in locals():
                os.remove(subtitle_path)
        except OSError:
            pass

        loading.print_message(colors.red(f"yt-dlp scraper failed - {e}"))
        return None


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

    return json.loads(output)


def video_transcript(url, always_use_yt_dlp=False):
    output = ""
    try:
        if not always_use_yt_dlp:
            video_id = url.replace(" ", "").split("v=")[1]

            # https://github.com/jdepoix/youtube-transcript-api
            content = YouTubeTranscriptApi.get_transcript(video_id)

            for line in content:
                output = output + line["text"] + " "
        else:
            raise Exception("Forcing use of yt-dlp-based scraper")
    except Exception as e:
        if not always_use_yt_dlp:
            loading.print_message(
                colors.yellow("Switching from API scraper to yt-dlp-based scraper")
            )
        output = yt_dlp_transcript_extractor(url, "en")

    return output


def extract_urls(text):
    url_pattern = r"https?://(?:www\.)?\S+"
    urls = re.findall(url_pattern, text)
    return urls


def remove_html(content):
    oline = content
    soup = BeautifulSoup(oline, "html.parser")
    for data in soup(["style", "script"]):
        data.decompose()
    tmp = " ".join(soup.stripped_strings)
    tmp = "".join(filter(lambda x: x in set(string.printable), tmp))
    tmp = re.sub(" +", " ", tmp)
    return tmp


def basic_scraper(url):
    try:
        response = utils.get_request(url)
        if response == None:
            raise Exception(f"http GET request failed due to an error code or timeout")
        return response.text
    except Exception as e:
        return f"An error occurred: {e}"


def process_url(url):
    try:
        if url.startswith(("https://www.youtube.com", "https://youtube.com")):
            meta_data = yt_dlp_scraper(url)
            content = {
                field: meta_data.get(field)
                for field in [
                    "title",
                    "duration",
                    "view_count",
                    "like_count",
                    "channel",
                    "channel_follower_count",
                    "uploader",
                    "upload_date",
                    "epoch",
                    "fulltitle",
                    "transcript",
                ]
            }
            content["description"] = re.sub(
                r"https?://\S+|www\.\S+", "", meta_data.get("description", "")
            )
        elif url.endswith(".pdf") or url.startswith(
            ("https://arxiv.org/pdf/", "http://arxiv.org/pdf/")
        ):
            content = scrape_pdf_url(url)
        elif url.startswith(
            (
                "https://www.vimeo.com",
                "https://vimeo.com",
                "https://www.twitch.tv",
                "https://twitch.tv",
                "https://www.dailymotion.com",
                "https://dailymotion.com",
                "https://www.dropout.tv",
                "https://dropout.tv",
                "https://www.linkedin.com",
                "https://linkedin.com",
                "https://www.twitter.com",
                "https://twitter.com",
                "https://x.com",
                "https://www.cbsnews.com",
                "https://cbsnews.com",
                "https://www.cnn.com",
                "https://cnn.com",
                "https://www.cnbc.com",
                "https://cnbc.com",
                "https://www.abc.com.au",
                "https://abc.com.au",
                "https://www.bbc.co.uk",
                "https://bbc.co.uk",
                "https://www.cartoonnetwork.com",
                "https://cartoonnetwork.com",
                "https://www.canalplus.fr",
                "https://canalplus.fr",
                "https://www.arte.tv",
                "https://arte.tv",
                "https://www.cbc.ca",
                "https://cbc.ca",
                "https://www.3sat.de",
                "https://3sat.de",
                "https://www.ard.de",
                "https://ard.de",
            )
        ):
            meta_data = yt_dlp_scraper(url=url, always_use_yt_dlp=True)
            content = {}
            for key in meta_data:
                if key.startswith("_") or meta_data[key] is None:
                    continue
                if isinstance(meta_data[key], (dict, list)):
                    continue
                content[key] = meta_data[key]
        else:
            content = remove_html(basic_scraper(url))
    except:
        content = None
    return url, content


def get_all_htmls(text):
    urls = None
    if type(text) == str:
        urls = list(set(extract_urls(text)))
        if not urls:
            return {}
    elif type(text) == list:
        urls = text
    else:
        raise Exception(f"{get_all_htmls.__name__}() only excepts type list or str")

    output = {}
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_url = {executor.submit(process_url, url): url for url in urls}
        for future in concurrent.futures.as_completed(future_to_url):
            url, content = future.result()
            output[url] = content

    return output


def scraped_prompt(prompt):
    htmls = get_all_htmls(prompt)
    if htmls == {}:
        return prompt

    new_prompt = """
Here is the content from the following url(s) in the form of a JSON:
```
{0}
```

Knowing this, can you answer the following prompt: {1}
""".format(
        json.dumps(htmls), prompt
    )

    return new_prompt


def scrape_pdf_url(url):
    try:
        response = utils.get_request(url)
        if response == None:
            raise Exception(f"http GET request failed due to an error code or timeout")

        if response.headers.get("Content-Type") == "application/pdf":
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
                tmp_file.write(response.content)
                tmp_path = tmp_file.name

            try:
                document = fitz.open(tmp_path)
                text = ""
                for page_num in range(len(document)):
                    page = document.load_page(page_num)
                    text += page.get_text()
                document.close()
                return text

            finally:
                # clean up temporary file
                try:
                    os.remove(tmp_path)
                except OSError as e:
                    loading.print_message(
                        colors.red(f"Failed to delete temporary PDF file: {e}")
                    )

        raise Exception(f"URL {url} is NOT a valid PDF file")
    except Exception as e:
        loading.print_message(colors.red(f"Failed to load PDF URL {url} due to {e}"))


def yt_dlp_scraper(url, always_use_yt_dlp=False):
    with concurrent.futures.ThreadPoolExecutor() as executor:
        get_meta_data = executor.submit(video_metadata, url)
        get_transcript = executor.submit(video_transcript, url, always_use_yt_dlp)

        if always_use_yt_dlp:
            get_web_page = executor.submit(basic_scraper, url)

        meta_data = get_meta_data.result()
        meta_data["transcript"] = get_transcript.result()

        if always_use_yt_dlp:
            meta_data["web_page_scrape"] = remove_html(get_web_page.result())

        return meta_data
