import concurrent.futures
import subprocess
import string
import json
import re
import os
import uuid

import fitz  # PyMuPDF
from bs4 import BeautifulSoup
from youtube_transcript_api import YouTubeTranscriptApi
from cha import colors, utils


def clean_subtitle_text(input_text):
    # NOTE: this function cleans the raw transcript outputed by yt-dlp
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
        # generate command and filepath
        # https://www.reddit.com/r/youtubedl/comments/15fcrmd/transcript_extract_from_youtube_videos_ytdlp/
        root_cmd = "yt-dlp --skip-download --write-subs --write-auto-subs"
        filename = f"cha_yt_{uuid.uuid4()}.srt"
        filepath = os.path.join(os.getcwd(), filename)
        cmd = f'{root_cmd} --sub-lang {lang} --sub-format ttml --convert-subs srt --output "{filepath}" "{url}"'

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
        # # TODO: a better solution is needed here
        # print(colors.red(f"yt-dlp scraper failed: {e}"))
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
        output = yt_dlp_transcript_extractor(url, "en")

    return output


def youtube_scraper(url):
    with concurrent.futures.ThreadPoolExecutor() as executor:
        get_meta_data = executor.submit(video_metadata, url)
        get_transcript = executor.submit(video_transcript, url)

        meta_data = get_meta_data.result()
        transcript = get_transcript.result()

        return {
            "title": meta_data.get("title"),
            # NOTE: removes urls from description
            "description": re.sub(
                r"https?://\S+|www\.\S+", "", meta_data.get("description", "")
            ),
            "duration": meta_data.get("duration"),
            "view_count": meta_data.get("view_count"),
            "like_count": meta_data.get("like_count"),
            "channel": meta_data.get("channel"),
            "channel_follower_count": meta_data.get("channel_follower_count"),
            "uploader": meta_data.get("uploader"),
            "upload_date": meta_data.get("upload_date"),
            "epoch": meta_data.get("epoch"),
            "fulltitle": meta_data.get("fulltitle"),
            "transcript": transcript,
        }


def twitter_scraper(url):
    with concurrent.futures.ThreadPoolExecutor() as executor:
        get_meta_data = executor.submit(video_metadata, url)
        get_transcript = executor.submit(yt_dlp_transcript_extractor, url)

        meta_data = get_meta_data.result()
        transcript = get_transcript.result()

        return {
            "platform": "Twitter/X",
            "title": meta_data.get("title"),
            "description": meta_data.get("description"),
            "uploader": meta_data.get("uploader"),
            "timestamp": meta_data.get("timestamp"),
            "channel_id": meta_data.get("channel_id"),
            "uploader_id": meta_data.get("uploader_id"),
            "uploader_url": meta_data.get("uploader_url"),
            "like_count": meta_data.get("like_count"),
            "repost_count": meta_data.get("repost_count"),
            "comment_count": meta_data.get("comment_count"),
            "duration": meta_data.get("duration"),
            "display_id": meta_data.get("display_id"),
            "webpage_url": meta_data.get("webpage_url"),
            "original_url": meta_data.get("original_url"),
            "webpage_url_domain": meta_data.get("webpage_url_domain"),
            "extractor": meta_data.get("extractor"),
            "extractor_key": meta_data.get("extractor_key"),
            "fulltitle": meta_data.get("fulltitle"),
            "duration_string": meta_data.get("duration_string"),
            "upload_date": meta_data.get("upload_date"),
            "epoch": meta_data.get("epoch"),
            "filename": meta_data.get("filename"),
            "transcript": transcript,
        }


def linkedin_scraper(url):
    try:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            get_meta_data = executor.submit(video_metadata, url)
            get_transcript = executor.submit(yt_dlp_transcript_extractor, url)

            meta_data = get_meta_data.result()
            transcript = get_transcript.result()

            video_content = {
                "platform": "LinkedIn",
                "title": meta_data.get("title"),
                "description": meta_data.get("description"),
                "like_count": meta_data.get("like_count"),
                "display_id": meta_data.get("display_id"),
                "webpage_url": meta_data.get("webpage_url"),
                "original_url": meta_data.get("original_url"),
                "webpage_url_domain": meta_data.get("webpage_url_domain"),
                "extractor": meta_data.get("extractor"),
                "extractor_key": meta_data.get("extractor_key"),
                "fulltitle": meta_data.get("fulltitle"),
                "epoch": meta_data.get("epoch"),
                "filename": meta_data.get("filename"),
                "transcript": transcript,
            }
    except:
        video_content = None

    try:
        content = remove_html(basic_scraper(url))
    except:
        content = None

    return {
        "post": content,
        "video": video_content,
    }


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


def format_type(url):
    if url.startswith("https://www.linkedin.com"):
        return "linkedin"
    if url.startswith("https://www.twitter.com") and url.startswith("https://x.com"):
        return "twitter"
    if url.startswith("https://www.youtube.com/watch?v"):
        return "youtube"
    if (
        url.endswith(".pdf")
        or url.startswith("https://arxiv.org/pdf/")
        or url.startswith("http://arxiv.org/pdf/")
    ):
        return "pdf"
    return "unknown"


def process_url(url):
    try:
        video_format = format_type(url)

        if video_format == "youtube":
            content = youtube_scraper(url)
        elif video_format == "pdf":
            content = scrape_pdf_url(url)
        elif video_format == "twitter":
            content = twitter_scraper(url)
        elif video_format == "linkedin":
            content = linkedin_scraper(url)
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
            filename = f"cha_{uuid.uuid4()}.pdf"
            with open(filename, "wb") as file:
                file.write(response.content)

            # extract text from the PDF
            document = fitz.open(filename)
            text = ""
            for page_num in range(len(document)):
                page = document.load_page(page_num)
                text += page.get_text()

            # delete the PDF file
            os.remove(filename)

            return text

        raise Exception(f"URL {url} is NOT a valid PDF file")
    except Exception as e:
        print(colors.red(f"Failed to load PDF URL {url} due to {e}"))
