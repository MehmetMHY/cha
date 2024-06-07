import requests
import os

#######################################[Main-Chat-Logic]########################################

INITIAL_PROMPT = (
    "You are a helpful assistant who keeps your response short and to the point"
)
MULTI_LINE_SEND = "END"
MULI_LINE_MODE_TEXT = "!m"
CLEAR_HISTORY_TEXT = "!c"
IMG_GEN_MODE = "!i"
SAVE_CHAT_HISTORY = "!s"
EXIT_STRING_KEY = "!e"
ADVANCE_SEARCH_KEY = "!b"

#######################################[YouTube-Scrapper]#######################################


def build_youtube_scrape_cmd(url, filename):
    # CREDIT: https://www.reddit.com/r/youtubedl/comments/15fcrmd/transcript_extract_from_youtube_videos_ytdlp/
    return f"yt-dlp --write-auto-sub --convert-subs=srt --skip-download {url} -o {filename}"


########################################[Search-Config]#########################################

big_model = "gpt-4o"
cheap_model = "gpt-3.5-turbo"
cheap_model_max_token = int((16_385) * 0.99)  # account for some error


# NOTE: brave does not have a python SDK so thsi function was created
def brave_search(search_input):
    # (March 9, 2024) Setup Brave API key here:
    #       https://api.search.brave.com/app/dashboard

    params = {
        # (required) the user's search query term
        "q": search_input,
        # (optional) the search query country
        "country": "us",
        # (optional) the search language preference
        "search_lang": "en",
        # (optional) user interface language preferred in response
        "ui_lang": "en-US",
        # (optional) the number of search results returned in response
        "count": 5,
        # (optional) the zero-based offset for pagination
        "offset": 0,
        # (optional) filters search results for adult content
        "safesearch": "moderate",
        # (optional) filters search results by when they were discovered
        "freshness": "none",
        # (optional) specifies if text decorations should be applied
        "text_decorations": 1,
        # (optional) specifies if spellcheck should be applied
        "spellcheck": 1,
        # (optional) a comma-delimited string of result types to include
        "result_filter": "web,news",
    }

    headers = {
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
        "X-Subscription-Token": os.environ.get("BRAVE_API_KEY"),
    }

    response = requests.get(
        "https://api.search.brave.com/res/v1/web/search", headers=headers, params=params
    )

    return response.json()


invalid_url_patterns = [
    r"/[^/?#]+\.[^/?#]+($|\?|#)",  # paths with a file extension
    r"/[^/?#]+/download($|\?|#)",  # urls with "download" in the last path segment
    r"/api/",  # urls that likely point to an API endpoint
    r"/[^/?#]+\.php($|\?|#)",  # php files (often dynamic but can be used for downloads)
]

excluded_extensions = [
    ".pdf",
    ".xml",
    ".css",
    ".docx",
    ".xlsx",
    ".pptx",
    ".zip",
    ".rar",
    ".exe",
    ".dmg",
    ".tar.gz",
    ".mp3",
    ".mp4",
    ".avi",
    ".mov",
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".bmp",
    ".csv",
    ".json",
    ".txt",
    ".ppt",
    ".pptx",
    ".doc",
    ".xls",
    ".rtf",
    ".7z",
    ".iso",
    ".wav",
    ".mkv",
]
