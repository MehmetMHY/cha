# TOOL IMPORTING LOGIC CONFIGURATION (DO NOT EDIT)

import os, sys

ROOT = os.path.dirname(__file__)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# LOAD EXTERNAL TOOLS (EDIT AS NEEDED)

from tools.weather.main import UsersCurrentWeatherStats

EXTERNAL_TOOLS = [UsersCurrentWeatherStats()]

# OVERRIDE DEFAULT CONFIG CHA VARIABLES (EDIT AS NEEDED)

CHA_DEFAULT_SHOW_PRINT_TITLE = False

CHA_LOCAL_SAVE_ALL_CHA_CHATS = True

"""
NOTE - PLEASE READ

For the local models to work, you will have to do the following:

1. Install Ollama: https://ollama.com/

2. Install Gemma model:

    ```
    ollama run gemma3:1b
    ```
"""

# NOTE: to use Cha fully local and open source, set `CHA_LOCAL_MODE` to `true` or just move all the variables below out of the if statement
# NOTE: before doing this, make sure to install Ollama (https://ollama.com/)
# NOTE: after installing Ollama, install the open-source LLM model -> ollama run gemma3:1b
if str(os.getenv("CHA_LOCAL_MODE")).lower() == "true":
    CHA_CURRENT_PLATFORM_NAME = "ollama"
    CHA_DEFAULT_MODEL = "gemma3:1b"
    CHA_DEFAULT_IMAGE_MODEL = "gemma3:1b"
    DEFAULT_SEARCH_BIG_MODEL = "gemma3:1b"
    DEFAULT_SEARCH_SMALL_MODEL = "gemma3:1b"
    DEFAULT_SEARCH_MAX_TOKEN_LIMIT = 8192
    DEFAULT_SEARCH_RESULT_COUNT = 2
    DEFAULT_GEN_SEARCH_QUERY_COUNT = 2
