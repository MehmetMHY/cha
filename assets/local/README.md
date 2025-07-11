# Cha - External Tool Feature/Platform

## Last Updated

January 20, 2025

## About

Cha supports user-created external tools that can be dropped into your local Cha config and automatically be discovered by Cha if setup correctly. As of the latest version, Cha uses lazy loading for external tools to improve startup performance - tools are only loaded when actually used.

## First Step

Before doing anything, make sure Cha is installed and working. Refer to the main README for those details. Afterwards, if you have not done so already, run the following command:

```bash
cha -i
```

By running this command, if you have not done so already, it initializes Cha's config at your `$HOME` directory. When you run this command it will create the following file structure:

```bash
$HOME/.cha/
├── config.py
└── tools/
└── history/
```

The `config.py` file allows you to set and/or override the default global variables for Cha. The `tools/` directory is where you will store all of your tools. The `history/` directory is where all your chat histories with Cha are stored if enabled, which by default, it is not.

## Setting Up Your Tool Example

- **NOTE:** _If you want to use Cha entirely with open-source software and avoid closed-source dependencies (mainly OpenAI), really review the `config.py`. There are variables you can set to do this. By default Cha uses OpenAI but that is not permanent. Right now, the example config in `config.py` is set such that is you set an environment variable named `CHA_LOCAL_MODE` to `true`. But if you want to make this more permanent, just move all those variables in that if statement that checks the `CHA_LOCAL_MODE` environment variable outside of that if statement and remove that if statement. By doing this, you make Cha fully local and open-source without depending on any closed-source dependencies and/or providers like OpenAI._

In this directory (where this README is located), you'll find an example `config.py` and a `tools/` folder. The `config.py` file loads an example tool from `tools/`, disables the initial help message for every Cha interaction, and sets up Cha to record and save all your conversations in the `history/` directory.

To set up this example, move both the `config.py` file and the `tools/` directory into your `$HOME/.cha/` directory. Replace existing content if necessary, unless you want to preserve your current setup.

This example tool retrieves your current weather data and makes it available as context to Cha. To use it, run `!weather` in Cha and press ENTER. You can review the tool's code to learn how tools are implemented in Cha. This example demonstrates all possible variables you can set for tools in Cha, so refer to its code for details.

## Deeper Look

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
- `requirements.txt` — lists your tool's Python dependencies

Cha does not install dependencies automatically. The user is responsible for running:

```bash
pip install -r ~/.cha/tools/<tool_name>/requirements.txt
```

Also, make sure the following code is in your `$HOME/.cha/config.py` file:

```python
import os, sys

ROOT = os.path.dirname(__file__)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# Import lazy_tool for performance optimization
try:
    from cha.config import lazy_tool
except ImportError:
    def lazy_tool(module_path, class_name):
        return {"_lazy_tool": True, "module_path": module_path, "class_name": class_name}
```

This code allows your custom config file to load all your tools in this directory structure. To add/set tool(s), add something like the following to your config file below the code above:

```python
EXTERNAL_TOOLS = [lazy_tool("tools.weather.main", "UsersCurrentWeatherStats")]
```

In this example, you are loading the tool `weather` using lazy loading and adding it to the global variable `EXTERNAL_TOOLS` that Cha uses to determine what tools it can use. The lazy loading approach significantly improves Cha's startup time by only importing and instantiating tools when they are actually used.

**Note**: The old approach of directly importing and instantiating tools still works but is deprecated:

```python
# OLD APPROACH (still works but not recommended):
# from tools.weather.main import UsersCurrentWeatherStats
# EXTERNAL_TOOLS = [UsersCurrentWeatherStats()]

# NEW APPROACH (recommended for better performance):
EXTERNAL_TOOLS = [lazy_tool("tools.weather.main", "UsersCurrentWeatherStats")]
```

### Tool Spec

Each tool must implement a single class that defines its behavior.

#### Required in `__init__`

| Attribute          | Type | Required | Description                       |
| ------------------ | ---- | -------- | --------------------------------- |
| `self.name`        | str  | Yes      | Human-readable name of your tool  |
| `self.description` | str  | Yes      | One-liner summary                 |
| `self.alias`       | str  | Yes      | The CLI command to call your tool |

#### Optional in `__init__`

| Attribute                     | Type | Default | Description                                     |
| ----------------------------- | ---- | ------- | ----------------------------------------------- |
| `self.include_history`        | bool | False   | If the chat history is passed into the tool     |
| `self.timeout_sec`            | int  | 15      | Timeout in seconds before Cha cancels your tool |
| `self.pipe_input`             | bool | False   | Whether to pass the user's raw input            |
| `self.pipe_output`            | bool | True    | Whether the output is fed back into the chat    |
| `self.show_loading_animation` | bool | True    | Weather or not to show loading animation        |

## Required Method: `execute(self, **kwargs)`

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

- If `pipe_input` is `True`, Cha will include the user's message as `piped_input`.
- If `include_history` is set, `chat_history` will be passed in.
- If `execute()` returns `None`, Cha assumes your tool failed.

## Example Tool

```python
# ~/.cha/tools/echo/main.py

class EchoTool:
    def __init__(self):
        self.name = "Echo Tool"
        self.description = "Repeats whatever the user just said."
        self.alias = "!echo"

        self.pipe_input = True
        self.include_history = True
        self.timeout_sec = 10
        self.pipe_output = True

    def execute(self, **kwargs):
        piped_input = kwargs.get("piped_input")
        if piped_input:
            return f"You said: {piped_input}"
        return "Nothing to echo!"
```

## Registering Tools

In `~/.cha/config.py`, register your tool using the lazy loading approach for optimal performance:

```python
import os, sys

ROOT = os.path.dirname(__file__)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# Import lazy_tool for performance optimization
try:
    from cha.config import lazy_tool
except ImportError:
    def lazy_tool(module_path, class_name):
        return {"_lazy_tool": True, "module_path": module_path, "class_name": class_name}

EXTERNAL_TOOLS = [
    lazy_tool("tools.echo.main", "EchoTool"),
    # other tools…
]
```

Cha will automatically load and instantiate the tool class when it's first used. The `alias` (`!echo`) is what users type to call it.

## Example `requirements.txt`

```txt
requests==2.32.3
beautifulsoup4==4.13.4
```

Let users know to install it with:

```bash
pip install -r ~/.cha/tools/echo/requirements.txt
```

## Best Practices

- Always test your tool using `python main.py` before registering.
- Avoid long-running logic unless your timeout is adjusted.
- Keep your `description` short — it is shown in tool help prompts.
- Tools that rely on prior messages (like summary/chat) should set `include_history`.
- Use the `lazy_tool()` approach for better startup performance instead of direct imports.
- Set `show_loading_animation = False` in your tool if it prints output directly (to avoid interference with loading animations).
