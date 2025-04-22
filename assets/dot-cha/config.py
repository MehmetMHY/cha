####################################[IMPORT-LOGIC-CONFIGURATION]####################################

import os, sys

ROOT = os.path.dirname(__file__)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

##################################[LOADING-EXTERNAL-TOOLS-CONFIG]###################################

from tools.weather.main import UsersCurrentWeatherStats

EXTERNAL_TOOLS = [UsersCurrentWeatherStats()]

################################[OVERRIDE-DEFAULT-CONFIG-VARIABLES]#################################

CHA_DEFAULT_SHOW_PRINT_TITLE = False

CHA_LOCAL_SAVE_ALL_CHA_CHATS = True
