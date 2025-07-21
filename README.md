# Cha

![image](https://github.com/user-attachments/assets/03eff35f-1489-49a8-9e3f-23723f1b1c1c)

Check out the complete [demo](https://www.youtube.com/watch?v=7zG8iFZjKtM)

## Overview

Cha is an open-source command-line tool that simplifies interactions with AI models from multiple providers including OpenAI, Anthropic, Groq, DeepSeek, and more. It allows users to efficiently engage with powerful language models directly from their terminal, with the ability to switch between different AI platforms mid-conversation while maintaining full chat history.

## Vision

Cha is a simple, lightweight CLI tool that provides access to powerful AI models directly from the terminal. Think of it like Vim versus Emacs: Cha focuses on simplicity and versatility, delivering essential functionality without overwhelming complexity. It's designed to fit seamlessly into your workflow, helping to reduce the need for developers to leave their terminals, making AI access and general knowledge querying straightforward and efficient.

## Features

- **CLI Chat Interface**: Communicate with OpenAI's models via commands `cha`.
- **Interactive & Non-interactive Modes**: Interact with models via chat interface, command-line arguments, or file input.
- **Multi-line Input Mode**: Simplifies complex input directly into the CLI. Type `\` to toggle multi-line mode, then `\` again to send.
- **Text-Editor Input Mode**: Use your system's terminal-based text editor for inputting your prompt, allowing easier input of complex and long prompts. This can be done though an argument or in interactive mode.
- **Web and YouTube Scraping**: Extract YouTube video transcripts, web PDFs, and general web content.
- **Voice Recording**: Record voice prompts and have them automatically transcribed to text using OpenAI's Whisper API or local whisper (set `TEXT_TO_SPEECH_MODEL = "local"` in config). Use `!r` in interactive mode or `cha -r` from command line.
- **Answer Search**: Simple implementation of an Answer-Search engine similar to Perplexity AI's solution. Use `!s` for deep search or `!s <query>` for quick search.
- **Estimate Tokens**: Option to estimate the token count for a file, string, or piped content.
- **Support for Multiple File Types**: Supports a variety of file types for input, including PDF, DOCX, XLSX, and common image formats, enabling seamless integration and processing of different kinds of content.
- **Platform Flexibility**: Switch between different AI platform providers offering OpenAI-compatible APIs using the `--platform` argument.
- **Switch Between Models**: Easily switch between models during a conversation using `!m`.
- **Switch Between Platforms**: Switch between different AI platforms (OpenAI, Anthropic, Groq, etc.) mid-conversation using `!p`, maintaining full chat history.
- **Codedump Feature**: Easily dump your entire code or a directory's content as one text file OR as context for your conversation.
- **Quick Web Search**: Well chatting you can ask a question/prompt and have Cha browse the web real quick before answering your question.
- **Export Markdown Fences**: If desired, export any Markdown fence in the latest message from a model to file(s).
- **Integrated Shell Access**: Execute shell commands directly within Cha's environment using `!x` (interactive shell) or `!x <command>` (run specific commands), enhancing workflow efficiency by providing immediate terminal access.
- **Auto URL Detection & Scraping**: Enable or disable automatic URL detection and content scraping with a toggle.
- **`fzf` for Selection**: Use `fzf` for interactive selection when searching chat history, traversing local files, or using the codedump feature.
- **Streamlined File Navigation**: Two modes for file selection - simple mode (`!l`) for quick selection in current directory, and advanced mode (`!f`) with full directory traversal, direct path support (`cd dirname`, `cd ..`), clean interface, and efficient file selection using `fzf`.
- **Dynamic Directory Navigation**: Navigate and change Cha's current directory mid-chat using `!n`. Supports direct path navigation (`!n /path/to/directory`) or interactive fzf-based navigation starting from your home directory. Track directory history and select final destination from visited directories.
- **Chat History Management**: Save, load, and search through your past conversations.
- **Local Configuration**: Customize Cha's behavior through local configuration files.
- **Interactive File Editor**: Edit files with AI assistance using `!v`. Select files, make AI-powered edits, view diffs, and access a shell for testing. Inside the editor, use `help` or `h` to see a full list of commands, including `diff` (`d`), `save` (`s`), `undo` (`u`), running shell commands (`!x`), and using your terminal editor for long prompts (`!t`).
- **Export Responses to Files**: Export model responses to files. In interactive mode, use the export command to export the latest response. Use `all` for all responses in the history. Add the `single` argument to save the whole response as one file instead of extracting code blocks (e.g. `single` or `all single`).
- **Export Chat History**: Export your entire chat conversation as JSON (default) or as a readable text file with timestamps, platform/model information, and clear user/bot formatting using the `!w` command (use `!w text` or `!w txt` for text format).
- **Cancel Message**: Cancel a message before sending it by ending it with `!.`.

## Dependencies

Cha relies on a few external command-line tools for some of its features. Please ensure these are installed on your system for the best experience:

- **`fzf`**: Essential for all interactive selection features, such as history search (`!r`), file navigation (`!f`, `!n`), and the codedump (`!d`) helper. A recent version is highly recommended to ensure compatibility with all features.
- **`ripgrep` (`rg`)**: Required for the history search feature (`!r`) to function.
- **`bat`**: Used to provide syntax-highlighted previews within the history search feature (`!r`). Essential for enhanced readability and user experience during history browsing.
- **`netcat` (`nc`)**: Required for network connectivity checks and certain internal operations.

## Getting Started

### Installation

You can install Cha using one of the following methods

#### Using install.sh (Recommended)

Clone the repository and run the installation script:

```bash
git clone <repository-url>
cd <repository-directory>
./install.sh
```

This creates a local virtual environment, checks if all dependencies are setup correctly, and provides instructions for adding Cha to your PATH.

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

1. **Clone the Repository**:

   ```bash
   git clone <repository-url>
   cd <repository-folder>
   ```

2. **Install the Package**:

   ```bash
   pip3 install --upgrade .
   ```

3. **Install other dependencies**:

   ```bash
   # checkout docs for installing here: https://ffmpeg.org/
   brew install ffmpeg

   # checkout docs for installing here: https://github.com/junegunn/fzf
   brew install fzf

   # required for history search functionality (!r)
   # checkout docs for installing here: https://github.com/BurntSushi/ripgrep
   brew install ripgrep

   # required for history search preview functionality (!r)
   # checkout docs for installing here: https://github.com/sharkdp/bat
   brew install bat
   ```

### Configuration

1. **API Key Setup**: Cha requires an OpenAI API key, which you can obtain [here](https://platform.openai.com/api-keys).

2. **Setup your .env file**: Create a `.env` file in the root directory and add your keys:

   ```bash
   export OPENAI_API_KEY="YOUR_OPENAI_API_KEY"
   ```

3. **Apply the environment variables**

   ```bash
   source .env
   ```

### Final Steps

After installing and configuring everything, the final step is to run the checkup script to ensure everything is set up/installed correctly. You can ignore optional checkups/tests here, as those are not necessary for the core of Cha to function. Knowing this, to run these checkups/tests, use the following command:

```bash
python3 ./assets/checkup.py
```

If the checkups/tests look good, or you're okay with it, then start using Cha!

```bash
cha
```

You can check the instructions below for more details on what Cha can do and how you can use it!

### Usage

#### Basic Invocation

- `cha`
- `cha "<some question or request>"`
- Example:
  ```bash
  cha "in type script how can I check if .canvas.edges is an empty array?"
  ```

#### Code-Dump/Debug Flags

- `cha --codedump` or `cha -d` - Interactive mode (exclude/include selection)
- `cha --codedump=all` or `cha -d all` - Include everything automatically (respects .gitignore)
- `cha --codedump=stdout` or `cha -d stdout` - Print output to stdout instead of saving to file
- `cha --codedump=all,stdout` or `cha -d all,stdout` - Include everything and print to stdout

The codedump feature uses `fzf` for an improved file selection experience:

- Navigate directories with `cd` (supports direct paths like `cd dirname` and `cd ..`)
- Select files with `select` command
- Remove files from selection with `unselect` command
- Type `help` to see all available commands
- Clean interface that only shows directory path when it changes or selection count changes

#### Voice Recording

- `cha -r`
- Example:
  ```bash
  cha -r
  # Records voice, transcribes to text, and sends to AI model
  ```

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
# Start a chat
cha

# During the chat, switch to Anthropic
!p anthropic

# Switch to Groq with specific model
!p groq|llama-3.1-8b

# Switch back to OpenAI
!p openai

# Switch just the model within current platform
!m gpt-4o
```

All chat history is preserved when switching platforms, and exported chat history (`!w text`) includes platform/model information for each message.

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
- Perform a quick web search before answering your question/prompt (-b).
- Feeding in file input (-f).
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

Cha also supports and accepts additional parameters. Here is the help page for reference:

```txt
usage: cha [-h] [-l FILE] [-a] [-t] [-m MODEL] [-p [PLATFORM]] [-d [CODE_DUMP]]
           [-e] [-x SHELL_COMMAND] [-hs [{fuzzy,exact}]] [-r] [-v [EDITOR]]
           [-sm] [-ct] [-ocr OCR] [-i] [-P] [-V] [-lh LOAD_HISTORY_FILE]
           [string ...]

A command-line tool for interacting with AI models from multiple providers.

positional arguments:
  string                Non-interactive mode, feed a string into the model

options:
  -h, --help            Show this help message and exit.
  -l FILE, --load FILE  Load a file to send to the model (interactive: !l)
  -a, --answer          Run answer search (interactive: !s)
  -t, --ide             Use a terminal text editor for input (interactive: !t)
  -m MODEL, --model MODEL
                        Switch model (interactive: !m)
  -p [PLATFORM], --platform [PLATFORM]
                        Switch platform (interactive: !p)
  -d [CODE_DUMP], --codedump [CODE_DUMP]
                        Codedump a directory (interactive: !d). Options: all,
                        stdout, or combine with comma: all,stdout
  -e, --export          Export code blocks from the last response (interactive:
                        !e)
  -x SHELL_COMMAND, --shell SHELL_COMMAND
                        Execute a shell command (interactive: !x)
  -hs [{fuzzy,exact}], --history [{fuzzy,exact}]
                        Search history. 'fuzzy' (default), 'exact' for exact.
                        (interactive: !hs)
  -r, --record          Record voice prompt (interactive: !r)
  -v [EDITOR], --editor [EDITOR]
                        Run the interactive editor (interactive: !v)
  -sm, --select-model   Select a model from a list
  -ct, --tokens         Count tokens for the input
  -ocr OCR, --ocr OCR   Extract text from a file using OCR
  -i, --init            Initialize cha config directory
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

## Other Platform(s) Compatibility

Cha now supports switching between AI platforms using the `--platform` argument, enabling interoperability with OpenAI-compatible APIs.

```bash
cha -p
```

Running `cha -p` opens a menu to select a platform. To skip the menu, provide the base URL, environment variable name, and model name directly. For example, to use the `DeepSeek-V3` model from `together.ai`:

```bash
# Get and set the provider's API key env variable
export TOGETHER_API_KEY="..."

# Run cha with a different provider/platform
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

For more details, check out the documentation in [docs](./assets/local/README.md) and the example files in [assets/local/](./assets/local/).

If you have enabled the **save chat history locally** feature after configuring the local setup, but want to start a chat session that is not saved, you can use the following argument:

```bash
cha --private (-P)
```

Using this option will ensure your chat session is NOT saved locally. Think of it like Google Chrome's Incognito Mode but for Cha!

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

## Contributing

Any contribution is welcomed! Please feel free to submit issues or pull requests for any bugs or features.

## License

Cha is licensed under the MIT License. See [LICENSE](./LICENSE) for more details.
