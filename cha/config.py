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

#######################################[YouTube-Scraper]#######################################


def build_youtube_scrape_cmd(url, filename):
    # CREDIT: https://www.reddit.com/r/youtubedl/comments/15fcrmd/transcript_extract_from_youtube_videos_ytdlp/
    return f"yt-dlp --write-auto-sub --convert-subs=srt --skip-download {url} -o {filename}"
