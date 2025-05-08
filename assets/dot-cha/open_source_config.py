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

CHA_CURRENT_PLATFORM_NAME = "ollama"

CHA_DEFAULT_MODEL = "gemma3:1b"
