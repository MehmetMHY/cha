# TOOL IMPORTING LOGIC CONFIGURATION (DO NOT EDIT)

import os, sys

ROOT = os.path.dirname(__file__)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

try:
    from cha.config import lazy_tool
except ImportError:

    def lazy_tool(module_path, class_name):
        return {
            "_lazy_tool": True,
            "module_path": module_path,
            "class_name": class_name,
        }


# LOAD EXTERNAL TOOLS (EDIT AS NEEDED)

EXTERNAL_TOOLS = [lazy_tool("tools.weather.main", "UsersCurrentWeatherStats")]

# OVERRIDE DEFAULT CONFIG CHA VARIABLES (EDIT AS NEEDED)

CHA_DEFAULT_SHOW_PRINT_TITLE = False

CHA_LOCAL_SAVE_ALL_CHA_CHATS = True

"""
To run Cha fully local/open-source:

1. Install Ollama: https://ollama.com/

2. Install the following model:
    ```bash
    ollama run qwen3:0.6b
    ```
    
3. Copy the content from this file to $HOME/.cha/config.py

4. Enable open-source mode by EITHER:
    - Setting: export CHA_LOCAL_MODE="true"
    - OR moving all config variables outside any if-statement.

Cha will then use local, open-source models/software only!
"""
if str(os.getenv("CHA_LOCAL_MODE")).lower() == "true":
    CHA_CURRENT_PLATFORM_NAME = "ollama"
    CHA_DEFAULT_MODEL = "qwen3:0.6b"
    CHA_DEFAULT_IMAGE_MODEL = "qwen3:0.6b"
    DEFAULT_SEARCH_BIG_MODEL = "qwen3:0.6b"
    DEFAULT_SEARCH_SMALL_MODEL = "qwen3:0.6b"
    DEFAULT_SEARCH_MAX_TOKEN_LIMIT = 8192
    DEFAULT_SEARCH_RESULT_COUNT = 2
    DEFAULT_GEN_SEARCH_QUERY_COUNT = 2
