# links
OPENAI_DOCS_LINK = "https://platform.openai.com/docs/overview"
ANTHROPIC_DOCS_LINK = "https://docs.anthropic.com/en/api/getting-started"

# main chat short config
INITIAL_PROMPT = "You are a helpful assistant who provides concise, clear, and accurate answers. Be brief, but ensure the response fully addresses the question without leaving out important details"
MULTI_LINE_SEND = "END"
MULI_LINE_MODE_TEXT = "!m"
CLEAR_HISTORY_TEXT = "!c"
IMG_GEN_MODE = "!i"
SAVE_CHAT_HISTORY = "!s"
EXIT_STRING_KEY = "!e"
HELP_PRINT_OPTIONS_KEY = "!h"
LOAD_MESSAGE_CONTENT = "!l"
RUN_ANSWER_FEATURE = "!a"

CLA_MAX_TOKENS = 1024

# NOTE: last updated on 10-17-2024
CHA_DEFAULT_MODEL = "gpt-4o"
CLA_DEFAULT_MODEL = "claude-3-5-sonnet-20240620"

OPENAI_MODELS_TO_IGNORE = ["instruct", "realtime", "audio"]
OPENAI_MODELS_TO_KEEP = ["gpt"]

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

# NOTE: These sizes are valid for most image-generation models, but OpenAI's models support only a few
COMMON_IMG_GEN_RESOLUTIONS = [
    "256x256",
    "512x512",
    "768x768",
    "1024x1024",
    "1024x1792",
    "1792x1024",
    "2048x2048",
    "4096x4096",
]

REQUEST_DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

REQUEST_DEFAULT_TIMEOUT_SECONDS = 10

REQUEST_DEFAULT_RETRY_COUNT = 1

REQUEST_BACKOFF_FACTOR = 0.1

# answer feature config
DEFAULT_SEARCH_BIG_MODEL = "gpt-4o"
DEFAULT_SEARCH_SMALL_MODEL = "gpt-4o-mini"
DEFAULT_SEARCH_FRESHNESS_STATE = "none"
DEFAULT_SEARCH_MAX_TOKEN_LIMIT = 120_000
DEFAULT_SEARCH_RESULT_COUNT = 5
DEFAULT_SEARCH_TIME_DELAY = 1
DEFAULT_GEN_SEARCH_QUERY_COUNT = 3
VALID_FRESHNESS_IDS = {
    "pd": "past day",
    "pw": "past week",
    "pm": "past month",
    "py": "past year",
    "none": "all time",
}

# NOTE: do NOT modify the code below!
# NOTE: the logic below allows you to set your only config file path and load it in

import importlib.util
import os

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
