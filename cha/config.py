# NOTE: do NOT modify any of the "import" lines below, just the variables!
from pathlib import Path
import importlib.util
import os

from cha import local


def lazy_tool(module_path, class_name):
    return {"_lazy_tool": True, "module_path": module_path, "class_name": class_name}


# system prompt
INITIAL_PROMPT = """
You are a helpful assistant powered by Cha who provides concise, clear, and accurate answers. Be brief, but ensure the response fully addresses the question without leaving out important details.

Always return any code or file output in a Markdown code fence, with syntax ```<language or filetype>\n...``` so it can be parsed automatically. Only do this when needed, no need to do this for responses just code segments and/or when directly asked to do so from the user.
""".strip()

# editor system prompt
EDITOR_SYSTEM_PROMPT = """
You are a code editor. Modify the provided file according to the user's request. Return only the complete modified file content, no explanations or markdown formatting. Preserve all formatting and structure unless specifically requested to change it.
""".strip()

# key words
MULTI_LINE_SEND = "\\"
MULTI_LINE_MODE_TEXT = "\\"
CLEAR_HISTORY_TEXT = "!c"
SAVE_CHAT_HISTORY = "!w"
EXIT_STRING_KEY = "!q"
HELP_PRINT_OPTIONS_KEY = "!h"
LOAD_MESSAGE_CONTENT = "!l"
LOAD_MESSAGE_CONTENT_ADVANCED = "!f"
RUN_ANSWER_FEATURE = "!a"
TEXT_EDITOR_INPUT_MODE = "!t"
SWITCH_MODEL_TEXT = "!m"
SWITCH_PLATFORM_TEXT = "!p"
USE_CODE_DUMP = "!d"
EXPORT_FILES_IN_OUTPUT_KEY = "!e"
PICK_AND_RUN_A_SHELL_OPTION = "!x"
ENABLE_OR_DISABLE_AUTO_SD = "!u"
LOAD_HISTORY_TRIGGER = "!r"
RUN_EDITOR_ALIAS = "!v"
BACKTRACK_HISTORY_KEY = "!b"
CHANGE_DIRECTORY_ALIAS = "!n"
HELP_ALL_ALIAS = "[ALL]"
SKIP_SEND_TEXT = "!."

# aliases that don't require parameters by default
PARAMETER_LESS_ALIASES = [
    CLEAR_HISTORY_TEXT,
    EXIT_STRING_KEY,
    LOAD_MESSAGE_CONTENT,
    LOAD_MESSAGE_CONTENT_ADVANCED,
    RUN_ANSWER_FEATURE,
    TEXT_EDITOR_INPUT_MODE,
    SWITCH_MODEL_TEXT,
    SWITCH_PLATFORM_TEXT,
    USE_CODE_DUMP,
    ENABLE_OR_DISABLE_AUTO_SD,
    RUN_EDITOR_ALIAS,
    BACKTRACK_HISTORY_KEY,
    CHANGE_DIRECTORY_ALIAS,
    SKIP_SEND_TEXT,
    HELP_PRINT_OPTIONS_KEY,
]

# last updated on 4-10-2024
CHA_DEFAULT_MODEL = "gpt-4.1"
CHA_DEFAULT_IMAGE_MODEL = "gpt-4o"
CHA_DEBUG_MODE = False
CHA_STREAMING_ERROR_LIMIT = 5
CHA_CURRENT_PLATFORM_NAME = "openai"

# local config variables
CHA_DEFAULT_SHOW_PRINT_TITLE = True
CHA_LOCAL_SAVE_ALL_CHA_CHATS = False
CHA_SHOW_VISITED_DIRECTORIES_ON_EXIT = True

# shell command security config, block only very dangerous commands
BLOCKED_SHELL_COMMANDS = [
    "sudo",
    "su",
    # "rm",
    # "rmdir",
    "dd",
    "mkfs",
    "fdisk",
    "format",
    "shutdown",
    "reboot",
    "halt",
    "poweroff",
    "init",
    "kill",
    "killall",
    "pkill",
    "passwd",
    "chpasswd",
    "userdel",
    "groupdel",
    "deluser",
    "delgroup",
    "iptables",
    "ufw",
    "firewall-cmd",
    "pfctl",
    "del",
    "deltree",
    "rd",
    "erase",
]

# answer feature config
DEFAULT_SEARCH_BIG_MODEL = "gpt-4.1"
DEFAULT_SEARCH_SMALL_MODEL = "gpt-4.1-mini"
DEFAULT_SEARCH_FRESHNESS_STATE = "none"
DEFAULT_SEARCH_MAX_TOKEN_LIMIT = 1_000_000
DEFAULT_SEARCH_TIME_DELAY_SECONDS = 1
DEFAULT_SEARCH_RESULT_COUNT = 5
DEFAULT_GEN_SEARCH_QUERY_COUNT = 5
CHA_SEAR_XNG_BASE_URL = "http://localhost:8080"
CHA_USE_SEAR_XNG = False
CHA_SEAR_XNG_TIMEOUT = 30

# other random configs
OPENAI_MODELS_TO_KEEP = ["gpt", "o0", "o1", "o2", "o3", "o4", "o5", "o6", "o7"]
OPENAI_IGNORE_DATED_MODEL_NAMES = False
BY_PASS_SLOW_MODEL_DETECTION = False
OPENAI_MODELS_TO_IGNORE = [
    "instruct",
    "realtime",
    "audio",
    "tts",
    "image",
    "transcribe",
]

# terminal/console config
SUPPORTED_TERMINAL_IDES = ["vim", "nvim", "vi", "nano", "hx", "pico", "micro", "emacs"]
PREFERRED_TERMINAL_IDE = "vi"
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

# external, custom, 3rd party tools if defined by the user externally
EXTERNAL_TOOLS = []

# http request configs
REQUEST_DEFAULT_TIMEOUT_SECONDS = 10
REQUEST_DEFAULT_RETRY_COUNT = 1
REQUEST_BACKOFF_FACTOR = 0.1
REQUEST_DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

# codedump variables
NOTHING_SELECTED_TAG = "[NOTHING]"
EXIT_SELECTION_TAG = "[EXIT]"
FILES_TO_IGNORE = [
    ".DS_Store",
    ".env",
    ".env.local",
    ".env",
    ".env.local",
    ".env.development",
    ".env.production",
    ".env.test",
]
DIRS_TO_IGNORE = [
    # version control
    ".git/",
    ".hg/",
    ".svn/",
    "CVS/",
    # python
    "__pycache__/",
    ".venv/",
    "venv/",
    "env/",
    ".env/",
    "*.egg-info/",
    ".pytest_cache/",
    ".mypy_cache/",
    ".ruff_cache/",
    "htmlcov/",
    # nodejs
    "node_modules/",
    ".npm/",
    ".yarn/",
    # java/jvm, rust
    "target/",
    ".gradle/",
    # php, go, ruby
    "vendor/",
    # .net
    "obj/",
    ".vs/",
    # ide(s)
    ".idea/",
    ".vscode/",
    ".cursor/",
    # general build/output/temporary
    "build/",
    "dist/",
    "out/",
    "output/",
    "bin/",
    "logs/",
    "log/",
    "tmp/",
    "temp/",
    "coverage/",
    ".coverage/",
    ".cache/",
]
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


"""
Updated: March 2, 2025
Source: https://pypi.org/project/openai-whisper/
*--------*--------*--------*-------*------------*
| Model  | Params | VRAM   | Speed | Error Rate |
|--------|--------|--------|-------|------------|
| tiny   | 39M    | ~1 GB  | ~10x  | ~23.6%     |
| base   | 74M    | ~1 GB  | ~7x   | ~16.5%     |
| small  | 244M   | ~2 GB  | ~4x   | ~9.8%      |
| medium | 769M   | ~5 GB  | ~2x   | ~8.9%      |
| large  | 1,550M | ~10 GB | 1x    | ~7.9%      |
| turbo  | 809M   | ~6 GB  | ~8x   | ~7.7%      |
*--------*--------*--------*-------*------------*
"""
DEFAULT_WHISPER_MODEL_NAME = "tiny"

# support file formats
SUPPORTED_IMG_FORMATS = [".jpg", ".jpeg", ".png"]
SUPPORTED_PDF_FORMATS = [".pdf"]
SUPPORTED_DOC_FORMATS = [".doc", ".docx"]
SUPPORTED_SPREAD_SHEET_FORMATS = [".xls", ".xlsx"]
SUPPORTED_AUDIO_FORMATS = [
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

# last updated on 3-11-2025
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
    "anthropic": {
        "models": {
            "url": "https://api.anthropic.com/v1/models",
            "headers": {
                "x-api-key": f"{os.environ.get('ANTHROPIC_API_KEY')}",
                "anthropic-version": "2023-06-01",
            },
            "json_name_path": "data.id",
        },
        "base_url": "https://api.anthropic.com/v1/",
        "env_name": "ANTHROPIC_API_KEY",
        "docs": "https://docs.anthropic.com/",
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

"""
ascii, text based, terminal animations for loading animations
- https://stackoverflow.com/questions/2685435/cooler-ascii-spinners
- https://raw.githubusercontent.com/sindresorhus/cli-spinners/master/spinners.json
"""
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

# last updated on March 29, 2025
FILETYPE_TO_EXTENSION = {
    "python": ".py",
    "py": ".py",
    "bash": ".sh",
    "sh": ".sh",
    "shell": ".sh",
    "zsh": ".zsh",
    "fish": ".fish",
    "powershell": ".ps1",
    "ps1": ".ps1",
    "bat": ".bat",
    "cmd": ".cmd",
    "javascript": ".js",
    "js": ".js",
    "typescript": ".ts",
    "ts": ".ts",
    "coffee": ".coffee",
    "vue": ".vue",
    "jsx": ".jsx",
    "tsx": ".tsx",
    "java": ".java",
    "c": ".c",
    "h": ".h",
    "hpp": ".hpp",
    "c++": ".cpp",
    "cpp": ".cpp",
    "cxx": ".cpp",
    "cc": ".cpp",
    "cs": ".cs",  # C#
    "go": ".go",
    "golang": ".go",
    "php": ".php",
    "rb": ".rb",  # Ruby
    "ruby": ".rb",
    "swift": ".swift",
    "kotlin": ".kt",
    "kt": ".kt",
    "rs": ".rs",  # Rust
    "rust": ".rs",
    "dart": ".dart",
    "r": ".r",
    "m": ".m",  # MATLAB/Objective-C
    "matlab": ".m",
    "mm": ".mm",  # Objective-C++
    "scala": ".scala",
    "lua": ".lua",
    "perl": ".pl",
    "pl": ".pl",
    "pm": ".pm",
    "tcl": ".tcl",
    "groovy": ".groovy",
    "gradle": ".gradle",
    "clojure": ".clj",
    "clj": ".clj",
    "cljs": ".cljs",
    "cljc": ".cljc",
    "fsharp": ".fs",
    "fs": ".fs",
    "elixir": ".ex",
    "ex": ".ex",
    "exs": ".exs",
    "asp": ".asp",
    "aspx": ".aspx",
    "jsp": ".jsp",
    "sas": ".sas",
    "d": ".d",  # D language
    "pas": ".pas",  # Pascal
    "pp": ".pp",  # Free Pascal
    "asm": ".asm",  # Assembly
    "s": ".s",
    "v": ".v",  # Verilog
    "sv": ".sv",  # SystemVerilog
    "vhd": ".vhd",
    "vhdl": ".vhdl",
    "cl": ".cl",  # OpenCL
    "html": ".html",
    "htm": ".htm",
    "css": ".css",
    "sass": ".sass",
    "scss": ".scss",
    "xml": ".xml",
    "svg": ".svg",
    "svgz": ".svgz",
    "yaml": ".yaml",
    "yml": ".yml",
    "toml": ".toml",
    "ini": ".ini",
    "cfg": ".cfg",
    "conf": ".conf",
    "json": ".json",
    "json5": ".json5",
    "jsonc": ".jsonc",
    "sql": ".sql",
    "tsql": ".sql",
    "pgsql": ".sql",
    "db2": ".sql",
    "csv": ".csv",
    "tsv": ".tsv",
    "proto": ".proto",
    "proto3": ".proto",
    "ipynb": ".ipynb",
    "md": ".md",
    "markdown": ".md",
    "rst": ".rst",
    "org": ".org",
    "latex": ".tex",
    "tex": ".tex",
    "rmd": ".Rmd",
    "rmarkdown": ".Rmd",
    "rproj": ".Rproj",
    "properties": ".properties",
    "inf": ".inf",
    "plist": ".plist",
    "txt": ".txt",
    "text": ".txt",
    "plaintext": ".txt",
    "rtf": ".rtf",
    "doc": ".doc",
    "docx": ".docx",
    "odt": ".odt",
    "ppt": ".ppt",
    "pptx": ".pptx",
    "pdf": ".pdf",
    "xls": ".xls",
    "xlsx": ".xlsx",
    "ods": ".ods",
    "rtfd": ".rtfd",
    "man": ".man",
    "makefile": ".makefile",
    "dockerfile": ".dockerfile",
    "docker-compose": ".yml",
    "gitignore": ".gitignore",
    "gitattributes": ".gitattributes",
    "editorconfig": ".editorconfig",
    "eslint": ".eslintrc.js",
    "eslintjson": ".eslintrc.json",
    "npmrc": ".npmrc",
    "babelrc": ".babelrc",
    "prettierrc": ".prettierrc",
    "gradlew": ".gradlew",
    "env": ".env",
    "nvmrc": ".nvmrc",
    "npmignore": ".npmignore",
    "dockerignore": ".dockerignore",
    "clang-format": ".clang-format",
    "clang-tidy": ".clang-tidy",
    "desktop": ".desktop",
    "service": ".service",
    "socket": ".socket",
    "timer": ".timer",
    "target": ".target",
    "jpg": ".jpg",
    "jpeg": ".jpeg",
    "png": ".png",
    "gif": ".gif",
    "bmp": ".bmp",
    "webp": ".webp",
    "ico": ".ico",
    "tiff": ".tiff",
    "tga": ".tga",
    "psd": ".psd",
    "xcf": ".xcf",
    "exr": ".exr",
    "hdr": ".hdr",
    "mp4": ".mp4",
    "mkv": ".mkv",
    "mov": ".mov",
    "avi": ".avi",
    "mpg": ".mpg",
    "mpeg": ".mpeg",
    "flv": ".flv",
    "f4v": ".f4v",
    "swf": ".swf",
    "mp3": ".mp3",
    "wav": ".wav",
    "flac": ".flac",
    "ogg": ".ogg",
    "wma": ".wma",
    "ape": ".ape",
    "aiff": ".aiff",
    "au": ".au",
    "caf": ".caf",
    "mid": ".mid",
    "midi": ".midi",
    "xm": ".xm",
    "it": ".it",
    "s3m": ".s3m",
    "mod": ".mod",
    "zip": ".zip",
    "7z": ".7z",
    "gz": ".gz",
    "xz": ".xz",
    "lz": ".lz",
    "lzma": ".lzma",
    "lzo": ".lzo",
    "lzop": ".lzop",
    "cpio": ".cpio",
    "z": ".z",
    "tar": ".tar",
    "tgz": ".tgz",
    "bz2": ".bz2",
    "rar": ".rar",
    "ps": ".ps",
    "eps": ".eps",
    "ai": ".ai",
}

# NOTE: do NOT modify the code below because it allows the loading of custom configs if provided!

TOOL_MOST_HAVE_VARIABLES = {
    "name": {"type": str, "required": True},
    "description": {"type": str, "required": True},
    "alias": {"type": str, "required": True},
    "include_history": {"type": [bool, int], "required": False, "default": False},
    "timeout_sec": {"type": int, "required": False, "default": 15},
    "pipe_input": {"type": bool, "required": False, "default": False},
    "pipe_output": {"type": bool, "required": False, "default": True},
    "show_loading_animation": {"type": bool, "required": False, "default": True},
}

LOCAL_CHA_CONFIG_DIR = os.path.join(str(Path.home()), ".cha/")
LOCAL_CHA_CONFIG_HISTORY_DIR = os.path.join(LOCAL_CHA_CONFIG_DIR, "history/")
LOCAL_CHA_CONFIG_TOOLS_DIR = os.path.join(LOCAL_CHA_CONFIG_DIR, "tools/")
LOCAL_CHA_CONFIG_FILE = os.path.join(LOCAL_CHA_CONFIG_DIR, "config.py")

_external_config_loaded = False


def _load_external_config():
    global _external_config_loaded
    if _external_config_loaded:
        return

    CUSTOM_CONFIG_PATH = os.environ.get("CHA_PYTHON_CUSTOM_CONFIG_PATH")
    OVERRIGHT_CONFIG = None
    if CUSTOM_CONFIG_PATH and os.path.exists(CUSTOM_CONFIG_PATH):
        OVERRIGHT_CONFIG = CUSTOM_CONFIG_PATH
    elif LOCAL_CHA_CONFIG_FILE and os.path.exists(LOCAL_CHA_CONFIG_FILE):
        OVERRIGHT_CONFIG = LOCAL_CHA_CONFIG_FILE

    if OVERRIGHT_CONFIG:
        spec = importlib.util.spec_from_file_location(
            "external_config", OVERRIGHT_CONFIG
        )
        external_config = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(external_config)

        for key, value in external_config.__dict__.items():
            if key.isupper():
                globals()[key] = value

    _external_config_loaded = True


def get_external_tools_execute():
    _load_external_config()

    if len(globals().get("EXTERNAL_TOOLS", [])) > 0:
        return local.get_tools()
    return []


CUSTOM_CONFIG_PATH = os.environ.get("CHA_PYTHON_CUSTOM_CONFIG_PATH")
OVERRIGHT_CONFIG = None
if CUSTOM_CONFIG_PATH and os.path.exists(CUSTOM_CONFIG_PATH):
    OVERRIGHT_CONFIG = CUSTOM_CONFIG_PATH
elif LOCAL_CHA_CONFIG_FILE and os.path.exists(LOCAL_CHA_CONFIG_FILE):
    OVERRIGHT_CONFIG = LOCAL_CHA_CONFIG_FILE

if OVERRIGHT_CONFIG != None:
    spec = importlib.util.spec_from_file_location("external_config", OVERRIGHT_CONFIG)
    external_config = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(external_config)

    for key, value in external_config.__dict__.items():
        if key.isupper() and key != "EXTERNAL_TOOLS":
            globals()[key] = value

EXTERNAL_TOOLS_EXECUTE = []
