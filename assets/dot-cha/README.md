# Cha - External Tool Feature/Platform

## About

Cha supports user-created external tools that can be dropped into your local Cha config and automatically be discovered by Cha if setup correctly.

## First Step

Before doing anything, make sure Cha is installed and working, refer to the main README for those details. Afterwards, if you have not done so already, run the following command:

```bash
cha -i
```

By running this command, if you have not done so already, it initializes cha's config at your `$HOME` directory. When you run this command it will create the following file structure:

```bash
$HOME/.cha/
├── config.py
└── tools/
└── history/
```

The `config.py` file allows you to set and/or override the default global variables for Cha. The `tools/` directory is were you will store all of your tools in. And the `history/` directory is were all your chat histories with Cha are stored if ENABLED, which by default, it's not.

## Setting Up Your Tool Example

In this directory that this README is located contains an example `config.py` and `tools/` setup. The `config.py` loads the one example tool in `tools/`, disable the initial help print for every Cha interaction, and enabled Cha with recording/saving all of your conversation with Cha in the `history/` directory. For this example, move the `config.py` file and `tools/` directly to your `$HOME/.cha/` directly. Replace the content in that directly if needed, unless you don't want to do that.

Knowing this, in this example, the tool provided is a tool that allows you to get your current weather data in your location and provide it as context to Cha. To call it, you can just run `!weather` in Cha and hit ENTER. You can refer to this tool's code to understand how tools are setup for Cha to support. This example tool provides all the possible variables you can set for tools in Cha, so please review the code.

## Deeper Look

Below is a deeper look into how tools work in Cha.

### Directory Structure

Every external tool must live under this structure:

```bash
$HOME/.cha/
├── config.py
└── tools/
    ├── your_tool/
    │   ├── main.py
    │   └── requirements.txt
    └── another_tool/
        ├── main.py
        └── requirements.txt
```

- `main.py` — defines one class that follows the Cha Tool Spec (below)
- `requirements.txt` — lists your tool’s Python dependencies

> ⚠️ Cha **does not install dependencies automatically**. The user is responsible for running:
>
> ```bash
> pip install -r ~/.cha/tools/<tool_name>/requirements.txt
> ```

Also make sure the following code is in your `$HOME/.cha/config.py` file:

```py
import os, sys

ROOT = os.path.dirname(__file__)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
```

By having this code, it allows your custom config file to load all your tools in this directory structure. Then to add/set tool(s), add something like the following to your config file below the code you set above:

```py
from tools.weather.main import UsersCurrentWeatherStats

EXTERNAL_TOOLS = [UsersCurrentWeatherStats()]
```

In this example, you are loading the tool `weather` and added it to the global variable `EXTERNAL_TOOLS` that Cha uses to determine what tools it can use. The first code is something you should always include but the second code is just an example of how you can import your tool following the suggested directory structure. 

### Tool Spec

Each tool must implement **a single class** that defines its behavior.

#### ✅ Required in `__init__`

| Attribute          | Type  | Required | Description                                         |
| ------------------ | ----- | -------- | --------------------------------------------------- |
| `self.name`        | `str` | ✅       | Human-readable name of your tool                    |
| `self.description` | `str` | ✅       | One-liner summary                                   |
| `self.alias`       | `str` | ✅       | The CLI command to call your tool (e.g. `!weather`) |

#### ⚡ Optional in `__init__`

| Attribute              | Type   | Default | Description                                                  |
| ---------------------- | ------ | ------- | ------------------------------------------------------------ |
| `self.include_history` | `bool` | `False` | Controls if the current chat history is passed into the tool          |
| `self.timeout_sec`     | `int`  | `15`    | Timeout in seconds before Cha cancels your tool              |
| `self.pipe_input`      | `bool` | `False` | Whether to pass the user's raw input into your tool          |
| `self.pipe_output`     | `bool` | `True`  | Whether your tool’s output is fed back into the chat context |

## ⚡ Required Method: `execute(self, **kwargs)`

Every tool must define:

```python
def execute(self, **kwargs):
    # possible keys in kwargs:
    # - piped_input: str
    # - chat_history: List[dict]

    # MUST return:
    # - str (success)
    # - or None (signals an error)
```

- If `pipe_input` is `True`, Cha will include the user’s message as `piped_input`.
- If `include_history` is set, `chat_history` will be passed in.
- If `execute()` returns `None`, Cha assumes your tool failed.

## 🧩 Example Tool

```python
# ~/.cha/tools/echo/main.py

class EchoTool:
    def __init__(self):
        self.name = "Echo Tool"
        self.description = "Repeats whatever the user just said."
        self.alias = "!echo"

        self.pipe_input = True
        self.include_history = True  # full conversation history
        self.timeout_sec = 10
        self.pipe_output = True

    def execute(self, **kwargs):
        piped_input = kwargs.get("piped_input")
        if piped_input:
            return f"You said: {piped_input}"
        return "Nothing to echo!"
```

## 📥 Registering Tools

In `~/.cha/config.py`, import and register your tool class manually:

```python
from tools.echo.main import EchoTool

EXTERNAL_TOOLS = [
    EchoTool,
    # other tools…
]
```

Cha will automatically instantiate the class and hook it into the CLI. The `alias` (`!echo`) is what users type to call it.

## 📄 Example `requirements.txt`

```txt
requests==2.32.3
beautifulsoup4==4.13.4
```

Let users know to install it with:

```bash
pip install -r ~/.cha/tools/echo/requirements.txt
```

## 📝 Best Practices

- 🧩 Always test your tool using `python main.py` before registering.
- ⚠️ Avoid long-running logic unless your timeout is adjusted.
- 💬 Keep your `description` short — it’s shown in tool help prompts.
- 🧠 Tools that rely on prior messages (like summary/chat) should set `include_history`.
