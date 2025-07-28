# Cha

<a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="License: MIT"></a>
<a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.11+-blue.svg" alt="Python 3.11+"></a>
<a href="https://github.com/MehmetMHY/cha/stargazers"><img src="https://img.shields.io/github/stars/MehmetMHY/cha" alt="GitHub stars"></a>
<a href="https://github.com/MehmetMHY/cha/graphs/contributors"><img src="https://img.shields.io/github/contributors/MehmetMHY/cha" alt="Contributors"></a>

[![Demo GIF](https://github.com/user-attachments/assets/03eff35f-1489-49a8-9e3f-23723f1b1c1c)](https://www.youtube.com/watch?v=7zG8iFZjKtM)

## Table of Contents

- [Overview](#overview)
- [Vision](#vision)
- [Quick Start](#quick-start)
- [Features](#features)
- [Getting Started](#getting-started)
  - [Installation](#installation)
  - [Configuration](#configuration)
  - [Usage](#usage)
- [Platform Compatibility](#other-platforms-compatibility)
- [Development](#development)
- [Local Config](#local-config-optional)
- [Additional Documentation](#additional-documentation)
- [Cha vs Claude Code](#cha-vs-claude-code-july-2025)
- [Contributing](#contributing)
- [License](#license)

## Overview

Cha is an open-source command-line tool that simplifies interactions with AI models from multiple providers including OpenAI, Anthropic, Groq, DeepSeek, Ollama, and more. It allows users to efficiently engage with powerful language models directly from their terminal, with the ability to switch between different AI platforms mid-conversation while maintaining full chat history.

## Vision

Cha is a lightweight, focused CLI tool that provides direct terminal access to powerful AI models. Like Vim's philosophy of simplicity and versatility, Cha delivers essential functionality without overwhelming complexity while giving users full control over their AI interactions through transparency and explicit context management. It integrates seamlessly into developer workflows, minimizing context switching and empowering individuals to guide AI on their own terms with a flexible, user-driven experience without automated decisions or hidden costs.

## Quick Start

**Install:**

```bash
curl -sSL https://raw.githubusercontent.com/MehmetMHY/cha/main/install.sh | bash
```

**Configure:**

```bash
# set your openai api key or use ollama (https://ollama.com/) for local models
export OPENAI_API_KEY="your-api-key-here"
```

**Start chatting:**

```bash
cha "What are the main features of the Rust programming language?"
```

For detailed installation options and configuration, see [Getting Started](#getting-started).

## Features

- **CLI Chat Interface**: Communicate with AI models via the `cha` command.
- **Interactive & Non-interactive Modes**: Interact with models via chat interface, command-line arguments, or file input.
- **Multi-line Input Mode**: Simplifies complex input directly into the CLI. Type `\` to toggle multi-line mode, then `\` again to send.
- **Text-Editor Input Mode**: Use your system's terminal-based text editor for inputting your prompt, allowing easier input of complex and long prompts. This can be done through an argument or in interactive mode.
- **Web and YouTube Scraping**: Extract YouTube video transcripts, web PDFs, and general web content.
- **Voice Recording**: Record voice prompts and have them automatically transcribed to text using OpenAI's Whisper API or local whisper (set `TEXT_TO_SPEECH_MODEL = "local"` in config). Use `!r` in interactive mode or `cha -r` from command line.
- **Voice Output**: Read out the AI's response using a voice. Use `!o` in interactive mode or `cha --voice` from command line.
- **Web Search**: Quick web search (`!s`) and deep answer search (`!w`) similar to Perplexity's solution.
- **Estimate Tokens**: Option to estimate the token count for a file, string, or piped content.
- **Support for Multiple File Types**: Supports a variety of file types for input, including PDF, DOCX, XLSX, and common image formats, enabling seamless integration and processing of different kinds of content.
- **Platform Flexibility**: Switch between different AI platform providers offering OpenAI-compatible APIs using the `--platform` argument.
- **Switch Between Models**: Easily switch between models during a conversation using `!m`.
- **Switch Between Platforms**: Switch between different AI platforms (OpenAI, Anthropic, Groq, etc.) mid-conversation using `!p`, maintaining full chat history.
- **Codedump Feature**: Easily dump your entire code or a directory's content as one text file OR as context for your conversation.
- **Quick Web Search**: While chatting you can ask a question/prompt and have Cha browse the web real quick before answering your question using `!s` (quick search) or `!w` (deep answer search).
- **Export Markdown Fences**: If desired, export any Markdown fence in the latest message from a model to file(s).
- **Integrated Shell Access**: Execute shell commands directly within Cha's environment using `!x` (interactive shell) or `!x <command>` (run specific commands), enhancing workflow efficiency by providing immediate terminal access.
- **Auto URL Detection & Scraping**: Enable or disable automatic URL detection and content scraping with a toggle.
- **`fzf` for Selection**: Use `fzf` for interactive selection when searching chat history, traversing local files, or using the codedump feature.
- **Streamlined File Navigation**: Two modes for file selection: simple mode (`!l`) for quick selection in current directory, and advanced mode (`!f`) with full directory traversal, direct path support (`cd dirname`, `cd ..`), clean interface, and efficient file selection using `fzf`.
- **Dynamic Directory Navigation**: Navigate and change Cha's current directory mid-chat using `!n`. Supports direct path navigation (`!n /path/to/directory`) or interactive fzf-based navigation starting from your home directory. Track directory history and select final destination from visited directories.
- **Chat History Management**: Save, load, and search through your past conversations.
- **Local Configuration**: Customize Cha's behavior through local configuration files.
- **Interactive File Editor**: Edit files with AI assistance using `!v`. Select files, make AI-powered edits, view diffs, and access a shell for testing. Inside the editor, use `help` or `h` to see a full list of commands, including `diff` (`d`), `save` (`s`), `undo` (`u`), running shell commands (`!x`), and using your terminal editor for long prompts (`!t`).
- **Export Chat History**: Export chat history using `!e` with interactive fzf selection. Choose from individual chats, all chats as text, or complete history as JSON. The interface shows chat previews sorted by newest to oldest, with `[ALL]` and `[ALL JSON]` options for bulk exports.
- **Copy to Clipboard**: Copy one or more chat responses to the clipboard using `!y`. Select responses with `fzf`, edit them in your terminal editor, and the final content is copied for easy pasting.
- **Seamless Pipe Output**: Automatically detects when output is piped to another command and suppresses all UI elements (colors, loading animations, status messages), making Cha perfect for use in shell pipelines and automation scripts.
- **Cancel Message**: Cancel a message before sending it by ending it with `!.`.

## Getting Started

### Dependencies

Cha relies on several external command-line tools for optimal functionality. The installation script handles most of these automatically.

#### Required Dependencies

| Tool                 | Purpose                                            | Installation                                                     |
| -------------------- | -------------------------------------------------- | ---------------------------------------------------------------- |
| **`fzf`**            | Interactive selection (history, files, navigation) | `brew install fzf` (macOS)<br>`apt install fzf` (Ubuntu)         |
| **`ripgrep` (`rg`)** | History search functionality                       | `brew install ripgrep` (macOS)<br>`apt install ripgrep` (Ubuntu) |
| **`bat`**            | Syntax-highlighted previews                        | `brew install bat` (macOS)<br>`apt install bat` (Ubuntu)         |
| **`netcat` (`nc`)**  | Network connectivity checks                        | Usually pre-installed                                            |
| **`ffmpeg`**         | Voice recording and media processing               | `brew install ffmpeg` (macOS)<br>`apt install ffmpeg` (Ubuntu)   |

### Quick Install Commands

**macOS (Homebrew):**

```bash
brew install fzf ripgrep bat ffmpeg
```

**Ubuntu/Debian:**

```bash
sudo apt update && sudo apt install fzf ripgrep bat ffmpeg netcat-openbsd
```

**Arch Linux:**

```bash
sudo pacman -S fzf ripgrep bat ffmpeg openbsd-netcat
```

> **Note**: The `install.sh` script automatically detects and installs missing dependencies on supported systems.

## Getting Started

### Installation

#### Recommended Method: One-Command Install

The most reliable way to get up and running is with our one-command installer. It provides a clean, self-contained installation that won't interfere with other Python projects or system packages.

Open your terminal and run the following command:

```bash
curl -sSL https://raw.githubusercontent.com/MehmetMHY/cha/main/install.sh | bash
```

The script automates the entire setup process, including checking for dependencies, creating a dedicated environment, and making the `cha` command accessible system-wide. To update, simply run the command again.

#### Manual Installation (from Git)

If you prefer to clone the repository manually, you can still use the installation script. This is also a good option if you want to contribute to development.

```bash
git clone https://github.com/MehmetMHY/cha.git
cd cha
./install.sh
```

Running the script from the cloned repository will automatically pull the latest changes and update your installation.

### Alternative Installation Methods

If you prefer a different approach, the following options are available. Note that with these methods, you are responsible for managing dependencies and the Python environment.

#### Pip

If you have Python installed, you can install Cha via pip, which should be available by default:

```bash
pip install git+https://github.com/MehmetMHY/cha.git
```

#### Pipx

To install using pipx, first make sure you have [pipx](https://pipx.pypa.io/stable/installation/) installed, then run:

```bash
pipx install 'git+https://github.com/MehmetMHY/cha.git'
```

#### Uv

If you prefer using uv, ensure it is installed from [uv installation guide](https://github.com/astral-sh/uv). Then, execute:

```bash
uv pip install "git+https://github.com/MehmetMHY/cha.git"
```

#### Manually

1.  **Clone the Repository**:
    ```bash
    git clone https://github.com/MehmetMHY/cha.git
    cd cha
    ```
2.  **Install the Package**:
    ```bash
    pip3 install --upgrade .
    ```
3.  **Install other dependencies**:
    Make sure you have `ffmpeg`, `fzf`, `ripgrep`, and `bat` installed. You can find installation instructions in the [Dependencies](#dependencies) section.

### Updating and Uninstalling

#### Updating

To update `cha` to the latest version, simply run the installation command again:

```bash
curl -sSL https://raw.githubusercontent.com/MehmetMHY/cha/main/install.sh | bash
```

The script will safely update your existing installation.

If you installed manually from a git clone, you can update by running the script from within your local repository directory:

```bash
# cd /path/to/your/cha-repository
./install.sh
```

#### Uninstalling

The process is straightforward. Just remove the installation directory and the symbolic link.

```bash
rm -rf "$HOME/.cha"
# for some setups, you may need to run the next command with sudo
rm /usr/local/bin/cha
```

#### Alternative Methods

- **To Update**:
  - **Pip**: `pip install --upgrade git+https://github.com/MehmetMHY/cha.git`
  - **Pipx**: `pipx upgrade cha`
  - **Uv**: `uv pip install --upgrade "git+https://github.com/MehmetMHY/cha.git"`
- **To Uninstall**:
  - **Pip**: `pip uninstall cha`
  - **Pipx**: `pipx uninstall cha`
  - **Uv**: `uv pip uninstall cha`

### Configuration

#### 1. API Key Setup

Cha requires an OpenAI API key at minimum. You can obtain one from the [OpenAI Platform](https://platform.openai.com/api-keys).

#### 2. Environment Variables

Create a `.env` file in your project directory or set environment variables directly:

```bash
# required openai api key
export OPENAI_API_KEY="sk-your-openai-api-key-here"

# optional additional platform keys
export ANTHROPIC_API_KEY="your-anthropic-key"
export GROQ_API_KEY="your-groq-key"
export DEEPSEEK_API_KEY="your-deepseek-key"
export TOGETHER_API_KEY="your-together-ai-key"
export GEMINI_API_KEY="your-gemini-key"
export XAI_API_KEY="your-xai-key"
```

#### 3. Apply Configuration

**Option A: Source the .env file**

```bash
source .env
```

**Option B: Add to your shell profile**

```bash
# add to ~/.bashrc, ~/.zshrc, or ~/.profile
echo 'export OPENAI_API_KEY="your-key-here"' >> ~/.zshrc
source ~/.zshrc
```

### Verify Setup

The `install.sh` script runs a verification check automatically. For manual installations, you can run the checkup script from the cloned directory to ensure your environment and API keys are configured correctly:

```bash
python3 ./assets/utils/checkup.py
```

> **Note**: Optional checkups can be ignored as they're not required for core functionality.

Once your setup is configured and verified, you can start using Cha:

```bash
cha
```

Refer to the [Usage](#usage) section below for detailed instructions and examples.

### Usage

#### Basic Invocation

- `cha`
- `cha "<some question or request>"`
- Example:
  ```bash
  cha "in type script how can I check if .canvas.edges is an empty array?"
  ```

#### Code-Dump/Debug Flags

The codedump feature allows you to package your codebase or specific files/directories into a single text file for AI analysis or documentation purposes. It supports multiple modes for maximum flexibility.

##### Basic Usage

- `cha --codedump` or `cha -d` - Interactive mode (exclude/include selection using fzf)
- `cha --codedump=all` or `cha -d all` - Include everything automatically (respects .gitignore)
- `cha --codedump=stdout` or `cha -d stdout` - Print output to stdout instead of saving to file
- `cha --codedump=all,stdout` or `cha -d all,stdout` - Include everything and print to stdout
- `cha --codedump=compress` or `cha -d compress` - Interactive mode with content compression

##### Specific Includes

The codedump feature supports specifying exactly which files and directories to include, perfect for developers who need precise control over what gets packaged.

**Basic Specific Includes:**

```bash
# include specific files
cha -d "include:src/main.py,config.py"

# include entire directories
cha -d "include:src/,tests/"

# mix files and directories
cha -d "include:src/core.py,tests/,docs/README.md"
```

**Advanced Patterns:**

```bash
# include with glob patterns
cha -d "include:src/**/*.py,*.md"

# include all javascript and typescript files
cha -d "include:*.js,*.ts,src/**/*.jsx"

# include specific subdirectories
cha -d "include:src/components/,src/utils/,tests/unit/"
```

**Combining with Output Options:**

```bash
# include specific files and output to stdout
cha -d "include:src/main.py,config.py,stdout"

# include directory with stdout output
cha -d "include:src/,stdout"

# include patterns and save to file (default)
cha -d "include:src/**/*.py,*.md"

# include specific files with compression
cha -d "include:src/main.py,config.py,compress"

# include all with compression and stdout output
cha -d "all,compress,stdout"
```

**Complex Real-World Examples:**

```bash
# frontend project: include react components and styles
cha -d "include:src/components/,src/styles/,public/index.html,package.json"

# backend api: include core logic and configs
cha -d "include:src/controllers/,src/models/,src/routes/,config/,*.json,stdout"

# python project: include source and tests
cha -d "include:src/,tests/,*.py,requirements.txt,README.md"

# documentation and config files only
cha -d "include:*.md,*.yml,*.json,docs/,stdout"
```

**Pattern Matching Rules:**

1. **Exact matches**: `config.py` matches exactly `config.py`
2. **Directory includes**: `src/` includes all files under the `src/` directory
3. **Glob patterns**: `*.py` matches all Python files in the current directory
4. **Recursive patterns**: `src/**/*.py` matches all Python files in `src/` and its subdirectories
5. **Mixed patterns**: You can combine exact files, directories, and glob patterns in one command

**Interactive Mode (Original):**

The codedump feature uses `fzf` for an improved file selection experience when using interactive mode:

- Navigate directories with `cd` (supports direct paths like `cd dirname` and `cd ..`)
- Select files with `select` command
- Remove files from selection with `unselect` command
- Type `help` to see all available commands
- Clean interface that only shows directory path when it changes or selection count changes

**Multiple Modes Available:**

The codedump feature offers several modes to suit different workflows:

- `cha -d` (interactive exclude/include selection)
- `cha -d all` (include all files)
- `cha -d stdout` (interactive with stdout output)
- `cha -d all,stdout` (include all with stdout output)

The `include:` syntax provides precise control when you know exactly what you want to include, while the interactive mode remains available for exploration and discovery.

#### Voice Recording

- `cha -r`
- Example:
  ```bash
  cha -r
  # records voice, transcribes to text, and sends to ai model
  ```

#### Voice Output

- `cha --voice "<prompt>"`
- In interactive mode, type `!o` to read out the last response using a voice.

#### Answer Search

- `cha -a`
- `cha -a "<question>"`
- Example:
  ```bash
  cha -a "what is the goal of life"
  ```

#### File Input with -l

- `cha -l <FILE>`
- Example:
  ```bash
  cha -l index.js
  ```

#### Local Text Editor (IDE) Input with -t

- `cha -t`

#### Interactive Editor with -v / --editor

- `cha -v`
- `cha --editor <FILE_PATH>`
- Example:
  ```bash
  cha -v
  # or
  cha --editor ./src/main.py
  ```

The interactive editor allows you to edit files with AI assistance. You can start it with or without a file path. If no path is provided, you can select a file using an `fzf`-based file picker.

#### Model Selection with -m

- `cha -m <MODEL_NAME>`
- Example:
  ```bash
  cha -m "o3-mini"
  ```

#### OCR (Extract Text from Files)

- `cha -ocr <FILE> [> <OUTPUT_FILE>]`
- Examples:
  ```bash
  cha -ocr ./README.md
  cha -ocr meme.jpg > output.txt
  ```

#### Platform Switching (-p) and Model Combined

- `cha -p "<PLATFORM_OR_URL|API_KEY_ENV>" -m "<MODEL_NAME>"`

  - Examples:
    ```bash
    cha -p "https://api.deepseek.com|DEEP_SEEK_API_KEY" -m "deepseek-chat"
    cha -p "llama3-70b-8192|GROQ_API_KEY" -m "llama3-70b-8192"
    ```

- `cha -p`

  - Dynamic platform switching with no need for the user to provide a base URL and model name.
  - Manually select a platform and model; refer to `./cha/config.py` to see all supported platforms.
  - Examples:
    ```bash
    cha -p
    ```

- `cha -p "<PLATFORM_NAME|OPTIONAL_MODEL_NAME>"`

  - Refer to `./cha/config.py` to see all supported platforms.
  - Here you can select a supported platform and a model on that platform in one line with no need for manually selecting a platform and/or model.
  - The model name is optional; you can just provide the platform name and manually select a model name. Or just provide both.
  - Please note, if the platform is not listed in the config or the model name is invalid, Cha will just error out.
  - Examples:

    ```bash
    # cleanly select a supported platform and the name of a model supported on the platform
    cha -p "groq|deepseek-r1-distill-llama-70b"

    # cleanly select just the platform and select a model from that platform manually with user input later on
    cha -p "groq"
    ```

#### History Search and Management

- `cha --continue` or `cha -c` - Resume the most recent conversation.
- `cha -hs [exact]` - Search and load previous chats. Fuzzy search is the default.
- `cha --load-history <file_path>` or `cha -lh <file_path>` - Load a specific chat history file.
- `cha` then type `!hs [exact]` during interactive mode to load a previous chat. Fuzzy search is the default.

#### Interactive Platform and Model Switching

During an interactive chat session, you can switch platforms and models on the fly:

- `!p` - Interactive platform selection (uses fzf for platform and model selection)
- `!p <platform_name>` - Switch to a specific platform (e.g. `!p anthropic`)
- `!p <platform_name>|<model_name>` - Switch to specific platform and model (e.g. `!p groq|llama-3.1-8b`)
- `!m` - Interactive model selection within current platform
- `!m <model_name>` - Switch to a specific model (e.g. `!m gpt-4`)

**Examples:**

```bash
# start a chat
cha

# during the chat, switch to anthropic
!p anthropic

# switch to groq with specific model
!p groq|llama-3.1-8b

# switch back to openai
!p openai

# switch just the model within current platform
!m gpt-4o
```

All chat history is preserved when switching platforms, and exported chat history (`!e`) includes platform/model information for each message.

#### Model Autoselection (--select-model)

- `cha --select-model`
- `cha --select-model <MODEL_NAME>`

#### Token Counting (--tokens) with a File

- `cha --tokens -l <FILE>`
- Example:
  ```bash
  cha --tokens -l README.md
  ```

#### Direct "How to" / "Make me" / "Craft me" Questions

These appear frequently with "cha" followed by a question/request referencing programming, shell commands, or general tasks, for example:

- `cha how many seconds is in a day`
- `cha in python how can I save a dict to a json`
- `cha craft me a unix command to find all Cargo.toml`
- `cha make me a simple flask API`

In essence, your unique "cha" CLI usage falls into these main patterns:

- Running "cha" with a direct query.
- Doing codedumps or debug dumps (-code_dump, -d).
- Performing deep answer searches (-a).
- Feeding in file input (-l).
- Specifying or switching models (-m, -sm).
- Running OCR operations (-ocr).
- Switching platforms (-p).
- Checking token counts (-t).
- Asking a broad variety of how-to / make-me requests directly after "cha ...".

Note that when you run Cha directly, meaning it conducts a single call to the model through the CLI as an argument, you can use the optional `-e` argument. This will export all code/file blocks in the model's last response that are enclosed in markdown fences. This feature makes it easy for Cha to generate files, such as a Python script, and have them accessible on you system (current directory) without needing to manually create a file, select, copy, and paste the content into a file. You can do this by running Cha like this (example):

```bash
cha -e write me python code to find the area of a circle
```

When you run the example command above, it will answer your question in one shot, then grab the code/file the model generated and save it to a file in your current directory. The file(s) it create will be named something like this: `export_a9570f7e.py`. Cha considers file extensions, so if the content is a text file, Go code, etc., it will include that file extension as part of the file name. With this, you can run the code/file and/or edit it on your system without needing to manually create a file if needed.

#### Powerful Pipeline Integration

Cha automatically detects when its output is being piped to another command and suppresses all UI elements, making it perfect for shell pipelines and automation. Here's a powerful example that creates intelligent git commits:

```bash
git add --all

git commit -m "$(
    {
        echo "here is my entire code... and here is all the changes i made... can you draft me a good git commit message for these changes with no emojis and simple and all lowercase."
        echo
        git diff HEAD
        echo
        git status --untracked-files=all
    } | cha | cat
)"
```

This command automatically generates intelligent commit messages by analyzing your code changes. The pipe detection ensures clean output without any UI interference, making Cha seamlessly integrate into your development workflow.

Cha also supports and accepts additional parameters. Here is the help page for reference:

```txt
usage: cha [-h] [-l FILE] [-a] [-t] [-m MODEL] [-p [PLATFORM]] [-d [CODE_DUMP]] [-e] [-x SHELL_COMMAND] [-hs [{fuzzy,exact}]] [-r] [--voice] [-v [EDITOR]]
           [-sm] [-ct] [-ocr OCR] [-i] [-c] [-P] [-V] [-lh LOAD_HISTORY_FILE]
           [string ...]

A command-line tool for interacting with AI models from multiple providers.

positional arguments:
  string                Non-interactive mode, feed a string into the model

options:
  -h, --help            Show this help message and exit.
  -l FILE, --load FILE  Load a file to send to the model (interactive: !l)
  -a, --answer          Run deep answer search (interactive: !w)
  -t, --ide             Use a terminal text editor for input (interactive: !t)
  -m MODEL, --model MODEL
                        Switch model (interactive: !m)
  -p [PLATFORM], --platform [PLATFORM]
                        Switch platform (interactive: !p)
  -d [CODE_DUMP], --codedump [CODE_DUMP]
                        Codedump a directory (interactive: !d). Options: all, stdout, compress, include:path1,path2 or combine: include:src/,stdout
  -e, --export          Export code blocks from the last response (interactive: !e)
  -x SHELL_COMMAND, --shell SHELL_COMMAND
                        Execute a shell command (interactive: !x)
  -hs [{fuzzy,exact}], --history [{fuzzy,exact}]
                        Search history. 'fuzzy' (default), 'exact' for exact. (interactive: !hs)
  -r, --record          Record voice prompt (interactive: !r)
  --voice               Read out the response from the model using a voice.
  -v [EDITOR], --editor [EDITOR]
                        Run the interactive editor (interactive: !v)
  -sm, --select-model   Select a model from a list
  -ct, --tokens         Count tokens for the input
  -ocr OCR, --ocr OCR   Extract text from a file using OCR
  -i, --init            Initialize cha config directory
  -c, --continue        Continue from the last chat session.
  -P, --private         Enable private mode (no history saved)
  -V, --version         Show version information
  -lh LOAD_HISTORY_FILE, --load-history LOAD_HISTORY_FILE
                        Load a chat history from a file.
```

## Development

For those interested in contributing or experimenting with Cha:

1. **Install Cha in Editable Mode**:

   ```bash
   pip install -e .
   ```

2. **Develop and Test**: Modify the source code and test changes using `cha`.

3. **(Optional) Load your Custom Configuration**: Use the `CHA_PYTHON_CUSTOM_CONFIG_PATH` environment variable to point to a custom `config.py` file that overrides default global variables. Set it using `export CHA_PYTHON_CUSTOM_CONFIG_PATH="/path/to/your/config.py"`. Ensure your defined variables are in uppercase.

4. **(Optional) Run code formatter if changes are made to Cha's codebase**: To keep the code clean and organized, make sure to run the Cha's code formatter which is **[fm](https://github.com/MehmetMHY/fm)**.

## Assets Overview

The `assets/` directory contains supplementary materials, tools, and examples to enhance Cha's functionality. Here's a quick rundown:

- **`assets/local/`**: Resources for setting up local configurations and custom external tools. It includes an example `weather` tool to demonstrate how you can extend Cha's capabilities.
- **`assets/macos/`**: A simple setup to create a macOS `.app` launcher for Cha using AppleScript, designed to open Cha in a Kitty terminal session.
- **`assets/sxng/`**: Scripts and documentation for integrating SearXNG, a self-hostable meta-search engine, as an alternative to DuckDuckGo for web-related features.
- **`assets/utils/`**: A collection of utility scripts for development and maintenance, including a `checkup.py` script to verify your setup and `update.py` to help manage package versions.

## Other Platform(s) Compatibility

Cha now supports switching between AI platforms using the `--platform` argument, enabling interoperability with OpenAI-compatible APIs.

```bash
cha -p
```

Running `cha -p` opens a menu to select a platform. To skip the menu, provide the base URL, environment variable name, and model name directly. For example, to use the `DeepSeek-V3` model from `together.ai`:

```bash
# get and set the provider's api key env variable
export TOGETHER_API_KEY="..."

# run cha with a different provider/platform
cha -p "https://api.together.xyz/v1|TOGETHER_API_KEY" -m "deepseek-ai/DeepSeek-V3"
```

Also, you can refer to the [config.py](./cha/config.py) file and the `THIRD_PARTY_PLATFORMS` variable to see all the other platforms you can try and/or use.

## Local Config (Optional)

Cha lets you store local files to tweak how it works, including:

- Setting your own variables or config for Cha
- Importing or building your own external tools to use inside Cha
- Saving all your conversations locally so you can do whatever you want with them

Once local history is enabled, features like browsing and searching your past chats are available using the `-hs` flag or `!r` during an interactive session.

By default, this is turned off, so there's no need to create any local files for Cha to run. You can set up the local configuration directory by running:

```bash
cha -i
```

### External Tools and Dependencies

If you installed Cha using the `install.sh` script and want to create custom external tools that require third-party Python packages, you'll need to install those packages in Cha's virtual environment. Since the install script creates an isolated environment at `$HOME/.cha/venv`, any external packages your tools need should be installed there:

```bash
# activate Cha's virtual environment
source "$HOME/.cha/venv/bin/activate"

# install your tool's dependencies
pip install requests beautifulsoup4 numpy  # example packages

# deactivate when done
deactivate
```

This only applies if you used the `install.sh` method. If you installed Cha via pip, pipx, or manually in your own environment, your external tools will automatically have access to packages installed in that same environment.

For more details, check out the documentation in [docs](./assets/local/README.md) and the example files in [assets/local/](./assets/local/).

If you have enabled the **save chat history locally** feature after configuring the local setup, but want to start a chat session that is not saved, you can use the following argument:

```bash
cha --private (-P)
```

Using this option will ensure your chat session is NOT saved locally. Think of it like Google Chrome's Incognito Mode but for Cha!

## Additional Documentation

For specific features and advanced configurations, refer to these additional documentation files:

- **[Local Configuration & External Tools](./assets/local/README.md)**: Complete guide for setting up local configurations, creating custom external tools, and extending Cha's functionality with user-defined tools.

- **[macOS App Setup](./assets/macos/README.md)**: Instructions for creating a macOS `.app` launcher that opens Cha in a Kitty terminal with your environment preloaded.

- **[SearXNG Integration](./assets/sxng/README.md)**: Setup guide for using SearXNG, a self-hostable meta-search engine, as an alternative to DuckDuckGo for web search features.

- **[Development Utilities](./assets/utils/README.md)**: Collection of utility scripts for testing, monitoring usage statistics, checking setup, and development maintenance.

- **[Weather Tool Example](./assets/local/tools/weather/README.md)**: Example external tool implementation that demonstrates how to create custom tools for Cha using the wttr.in weather API.

### SearXNG Search Engine Integration (Optional)

Cha can use [SearXNG](https://searxng.github.io/), an open-source meta-search engine you can self-host, for all web and answer search features. This is completely optional but recommended for heavy users or those who want full control. To enable SearXNG in Cha:

1. Follow the setup instructions in [`assets/sxng/README.md`](assets/sxng/README.md) (includes a one-command Docker setup and a Python usage example).
2. Set the following in your `$HOME/.cha/config.py`:

   ```bash
   CHA_USE_SEAR_XNG=True

   # change if your SearXNG runs elsewhere
   CHA_SEAR_XNG_BASE_URL="http://localhost:8080"
   ```

3. Now start using `cha` and you will see that the SearXNG engine will be used instead of DuckDuckGo.

If not enabled, Cha continues to use DuckDuckGo by default.

## Cha vs Claude Code (July 2025)

Cha takes a fundamentally different approach from autonomous AI coding CLIs like [Claude Code CLI](https://github.com/anthropics/claude-code), [Gemini CLI](https://github.com/google-gemini/gemini-cli), and [OpenAI Codex CLI](https://github.com/openai/codex).

### Key Differences

| Aspect                    | Cha                                      | Agentic CLIs (Claude Code, Gemini etc.)  |
| ------------------------- | ---------------------------------------- | ---------------------------------------- |
| **Control**               | Total user control at every step         | Automated workflow decisions             |
| **Background Processing** | No background AI workers                 | Smart agents make autonomous decisions   |
| **Context Management**    | Explicit user-controlled context         | AI managed context and file handling     |
| **Cost**                  | $1 to $20 per month for daily active use | $10 to $200+ per month for similar usage |
| **Editing**               | No surprise edits, user guided           | Autonomous code modifications            |
| **Use Case**              | Deep involvement, cost control           | Rapid prototyping, delegation            |

### When to Choose Cha

- **Minimal cost** with full transparency
- **Complete control** over every interaction
- **Deep involvement** in your development process
- **Explicit context management** for sensitive projects

### When to Choose Agentic Tools

- **Rapid prototyping** and fast iteration
- **Preference for AI automation** and delegation
- **Speed over cost** considerations

### Recommendations

There is no silver bullet when it comes to a tool. No tool is perfect and can account for every case scenario in their area/field. That same applies to Cha. Cha is great for cost-effective daily tasks and precise control while tools like Claude Code and Gemini CLI are great when the goal is to do more complex coding tasks across multiple files and environments, with the focus on fast development and automation. Use Cha when you want to reduce cost of using AI tools, choose agentic tools when you need rapid iteration and do not mind delegating control, and consider starting with Cha to learn AI interaction patterns before exploring agentic tools as your needs evolve.

## Contributing

Contributions are welcome and appreciated! Cha is an open-source project that benefits from community involvement.

### How to Contribute

1. **Report Issues**: Found a bug or have a feature request? [Open an issue](https://github.com/MehmetMHY/cha/issues)
2. **Submit Pull Requests**: Fork the repository, make your changes, and submit a PR
3. **Improve Documentation**: Help improve the README, add examples, or create tutorials
4. **Share Feedback**: Let us know how you're using Cha and what could be better

### Development Setup

```bash
# clone the repository
git clone https://github.com/MehmetMHY/cha.git
cd cha

# install in development mode
pip install -e .

# run the checkup to verify your setup
python3 assets/utils/checkup.py
```

### Code Standards

- Follow existing code style and conventions
- Run the code formatter [fm](https://github.com/MehmetMHY/fm) if making changes
- Test your changes thoroughly before submitting
- Update documentation as needed

### Community

- **Issues**: [GitHub Issues](https://github.com/MehmetMHY/cha/issues)
- **Discussions**: [GitHub Discussions](https://github.com/MehmetMHY/cha/discussions)
- **Demo**: [Watch the complete demo](https://www.youtube.com/watch?v=7zG8iFZjKtM)

## License

Cha is licensed under the MIT License. See [LICENSE](./LICENSE) for more details.
