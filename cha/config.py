# NOTE: do NOT modify any of the "import" lines below, just the variables!
import importlib.util
import os

# links
OPENAI_DOCS_LINK = "https://platform.openai.com/docs/overview"

# main chat short config
INITIAL_PROMPT = "You are a helpful assistant who provides concise, clear, and accurate answers. Be brief, but ensure the response fully addresses the question without leaving out important details"
MULTI_LINE_SEND = "END"
MULTI_LINE_MODE_TEXT = "!m"
CLEAR_HISTORY_TEXT = "!c"
SAVE_CHAT_HISTORY = "!s"
EXIT_STRING_KEY = "!e"
HELP_PRINT_OPTIONS_KEY = "!h"
LOAD_MESSAGE_CONTENT = "!l"
RUN_ANSWER_FEATURE = "!a"
TEXT_EDITOR_INPUT_MODE = "!t"
SWITCH_MODEL_TEXT = "!sm"
USE_CODE_DUMP = "!d"

# last updated on 11-19-2024
CHA_DEFAULT_MODEL = "gpt-4o"
CHA_DEFAULT_IMAGE_MODEL = "gpt-4o"

# answer feature config
DEFAULT_SEARCH_BIG_MODEL = "gpt-4o"
DEFAULT_SEARCH_SMALL_MODEL = "o3-mini"
DEFAULT_SEARCH_FRESHNESS_STATE = "none"
DEFAULT_SEARCH_MAX_TOKEN_LIMIT = 128_000
DEFAULT_SEARCH_TIME_DELAY_SECONDS = 1
DEFAULT_SEARCH_RESULT_COUNT = 5
DEFAULT_GEN_SEARCH_QUERY_COUNT = 15
DEFAULT_SPLIT_LOGIC_COUNT = 6

# other random configs
OPENAI_MODELS_TO_IGNORE = ["instruct", "realtime", "audio"]
FILES_TO_IGNORE = [".DS_Store", ".env", ".env.local"]
OPENAI_MODELS_TO_KEEP = ["gpt", "o0", "o1", "o2", "o3", "o4", "o5"]

# terminal/console config
SUPPORTED_TERMINAL_IDES = ["vim", "vi", "nano", "emacs", "pico", "micro"]
PREFERRED_TERMINAL_IDE = "vim"
MOVE_CURSOR_ONE_LINE = "\033[F"
HIDE_CURSOR = "\033[?25l"
SHOW_CURSOR = "\033[?25h"
CLEAR_LINE = "\033[K"
TERMINAL_THEME_CODES = {
    "reset": "\033[0m",
    "colors": {
        "red": "\033[91m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "magenta": "\033[95m",
        "cyan": "\033[96m",
        "white": "\033[97m",
        "black": "\033[30m",
    },
    "styles": {"bold": "\033[1m", "underline": "\033[4m"},
    "backgrounds": {
        "black": "\033[40m",
        "red": "\033[41m",
        "green": "\033[42m",
        "yellow": "\033[43m",
        "blue": "\033[44m",
        "magenta": "\033[45m",
        "cyan": "\033[46m",
        "white": "\033[47m",
    },
}

# http request configs
REQUEST_DEFAULT_TIMEOUT_SECONDS = 10
REQUEST_DEFAULT_RETRY_COUNT = 1
REQUEST_BACKOFF_FACTOR = 0.1
REQUEST_DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

# codedump variables
BINARY_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".bmp",
    ".tiff",
    ".ico",
    ".pdf",
    ".zip",
    ".tar",
    ".gz",
    ".svg",
    ".mp4",
    ".mp3",
    ".wav",
    ".ogg",
    ".mov",
    ".exe",
    ".dll",
    ".so",
    ".dylib",
    ".pyc",
    ".pkl",
    ".pickle",
    ".lock",
    ".woff",
    ".woff2",
    ".ttf",
    ".ds_store",
    ".env",
    ".env.local",
    ".env.development",
    ".env.production",
    ".env.test",
}


# Updated: March 2, 2025
# Source: https://pypi.org/project/openai-whisper/
# *--------*--------*--------*-------*------------*
# | Model  | Params | VRAM   | Speed | Error Rate |
# |--------|--------|--------|-------|------------|
# | tiny   | 39M    | ~1 GB  | ~10x  | ~23.6%     |
# | base   | 74M    | ~1 GB  | ~7x   | ~16.5%     |
# | small  | 244M   | ~2 GB  | ~4x   | ~9.8%      |
# | medium | 769M   | ~5 GB  | ~2x   | ~8.9%      |
# | large  | 1,550M | ~10 GB | 1x    | ~7.9%      |
# | turbo  | 809M   | ~6 GB  | ~8x   | ~7.7%      |
# *--------*--------*--------*-------*------------*
DEFAULT_WHISPER_MODEL_NAME = "tiny"
LOCAL_WHISPER_SUPPORTED_FORMATS = [
    ".mp3",
    ".mp4",
    ".wav",
    ".m4a",
    ".flac",
    ".ogg",
    ".webm",
]
SUPPORTED_VIDEO_FORMATS = [
    ".mp4",
    ".avi",
    ".mov",
    ".mkv",
    ".webm",
    ".flv",
    ".wmv",
    ".mpeg",
    ".mpg",
    ".m4v",
    ".ogv",
    ".3gp",
    ".3g2",
    ".asf",
    ".vob",
    ".rm",
    ".m2v",
    ".ts",
    ".mxf",
    ".f4v",
    ".divx",
    ".qt",
    ".amv",
    ".nsv",
    ".roq",
    ".svi",
    ".mod",
]

# last updated on 03-11-2025
SCRAPE_MODEL_NAME_FOR_PLATFORMS = "gpt-4o-mini"
THIRD_PARTY_PLATFORMS = {
    "groq": {
        "models": {
            "url": "https://api.groq.com/openai/v1/models",
            "headers": {
                "Authorization": f"Bearer {os.environ.get('GROQ_API_KEY')}",
                "Content-Type": "application/json",
            },
            "json_name_path": "data.id",
        },
        "base_url": "https://api.groq.com/openai/v1",
        "env_name": "GROQ_API_KEY",
        "docs": "https://console.groq.com/docs/overview",
    },
    "deepseek": {
        "models": {
            "url": "https://api.deepseek.com/models",
            "headers": {
                "Accept": "application/json",
                "Authorization": f"Bearer {os.environ.get('DEEP_SEEK_API_KEY')}",
            },
            "json_name_path": "data.id",
        },
        "base_url": "https://api.deepseek.com",
        "env_name": "DEEP_SEEK_API_KEY",
        "docs": "https://api-docs.deepseek.com/",
    },
    "together_ai": {
        "models": {
            "url": "https://api.together.xyz/v1/models",
            "headers": {
                "accept": "application/json",
                "authorization": f"Bearer {os.environ.get('TOGETHER_API_KEY')}",
            },
            "json_name_path": "id",
        },
        "base_url": "https://api.together.xyz/v1",
        "env_name": "TOGETHER_API_KEY",
        "docs": "https://docs.together.ai/docs/introduction",
    },
    "gemini": {
        "models": {
            "url": f"https://generativelanguage.googleapis.com/v1beta/models?key={os.environ.get('GEMINI_API_KEY')}",
            "headers": {},
            "json_name_path": "models.name",
        },
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "env_name": "GEMINI_API_KEY",
        "docs": "https://ai.google.dev/gemini-api/docs",
    },
    "ollama": {
        "models": {
            "url": "http://localhost:11434/api/tags",
            "headers": {},
            "json_name_path": "models.name",
        },
        "base_url": "http://localhost:11434/v1",
        "env_name": "ollama",
        "docs": "https://github.com/ollama/ollama/blob/main/docs/api.md",
    },
    "xai": {
        "models": {
            "url": "https://api.x.ai/v1/models",
            "headers": {
                "accept": "application/json",
                "authorization": f"Bearer {os.environ.get('XAI_API_KEY')}",
            },
            "json_name_path": "data.id",
        },
        "base_url": "https://api.x.ai/v1",
        "env_name": "XAI_API_KEY",
        "docs": "https://docs.x.ai/docs/overview",
    },
}

# urls that contain video data that can be scrapped using cha's scraper
VALID_VIDEO_ROOT_URL_DOMAINS_FOR_SCRAPING = [
    "https://www.youtube.com",
    "https://youtube.com",
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
]

# ascii, text based, terminal animations for loading animations
# - https://stackoverflow.com/questions/2685435/cooler-ascii-spinners
# - https://raw.githubusercontent.com/sindresorhus/cli-spinners/master/spinners.json
LOADING_ANIMATIONS = {
    "basic": ["|", "/", "-", "\\"],
    "star": ["✶", "✸", "✹", "✺", "✹", "✷"],
    "vertical_bar": [
        "▉",
        "▊",
        "▋",
        "▌",
        "▍",
        "▎",
        "▏",
        "▎",
        "▍",
        "▌",
        "▋",
        "▊",
        "▉",
    ],
    "dots": ["▖", "▘", "▝", "▗"],
    "rectangles": ["◰", "◳", "◲", "◱"],
    "circles": ["◴", "◷", "◶", "◵"],
    "halfcircles": ["◐", "◓", "◑", "◒"],
    "braille": [
        "⣾",
        "⣽",
        "⣻",
        "⢿",
        "⡿",
        "⣟",
        "⣯",
        "⣷",
        "⠁",
        "⠂",
        "⠄",
        "⡀",
        "⢀",
        "⠠",
        "⠐",
        "⠈",
    ],
}

# NOTE: do NOT modify the code below because it allows the loading of custom configs if provided!
CUSTOM_CONFIG_PATH = os.environ.get("CHA_PYTHON_CUSTOM_CONFIG_PATH")
if CUSTOM_CONFIG_PATH and os.path.exists(CUSTOM_CONFIG_PATH):
    spec = importlib.util.spec_from_file_location("external_config", CUSTOM_CONFIG_PATH)
    external_config = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(external_config)

    # update the current module's globals with values from the external file
    for key, value in external_config.__dict__.items():
        # assuming all config variables are in uppercase
        if key.isupper():
            globals()[key] = value
