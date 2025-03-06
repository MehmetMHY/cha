# Cha

## Overview

Cha is an open-source command-line tool that simplifies interactions with AI models from OpenAI. It allows users to efficiently engage with powerful language models directly from their terminal, enhancing development workflows.

## Vision

Cha is a simple, lightweight CLI tool that provides access to powerful AI models directly from the terminal. Think of it like Vim versus Emacs: Cha focuses on simplicity and versatility, delivering essential functionality without overwhelming complexity. It's designed to fit seamlessly into your workflow, helping to reduce the need for developers to leave their terminals, making AI access and general knowledge querying straightforward and efficient.

## Features

- **CLI Chat Interface**: Communicate with OpenAI's models via commands `cha`.
- **Interactive & Non-interactive Modes**: Interact with models via chat interface, command-line arguments, or file input.
- **Multi-line Input Mode**: Simplifies complex input directly into the CLI.
- **Text-Editor Input Mode**: Use your system's terminal-based text editor for inputting your prompt, allowing easier input of complex and long prompts.
- **Web and YouTube Scraping**: Extract YouTube video transcripts, web PDFs, and general web content.
- **Answer Search**: Simple implementation of an Answer-Search engine similar to Perplexity AI's solution.
- **Estimate Tokens**: Option to estimate the token count for a file, string, or piped content.
- **Support for Multiple File Types**: Supports a variety of file types for input, including PDF, DOCX, XLSX, and common image formats, enabling seamless integration and processing of different kinds of content.
- **Platform Flexibility**: Switch between different AI platform providers offering OpenAI-compatible APIs using the `--platform` argument.
- **Switch Between Models**: Easily switch between models during a conversation.
- **Code Dump Feature**: Easily dump your entire code or a directory's content as one text file OR as context for your conversation.
- **Browse Mode**: Enables fast automated web browsing to gather additional context for enhancements in response to user queries. It's quicker than the answer search engine, making it ideal for quick search-based questions.

## Getting Started

### Installation

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
# checkout docs for install details different systems: https://ffmpeg.org/
brew install ffmpeg
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

### Usage

#### Basic Invocation

- `cha`
- `cha "<some question or request>"`
- Example:
  ```bash
  cha "in type script how can I check if .canvas.edges is an empty array?"
  ```

#### Code-Dump/Debug Flags

- `cha --code_dump`
- `cha -d`

#### Answer Search

- `cha -a`
- `cha -a "<question>"`
- Example:
  ```bash
  cha -a "what is the goal of life"
  ```

#### File Input with -f

- `cha -f <FILE>`
- Example:
  ```bash
  cha -f index.js
  ```

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
- Dynamic platform switching with no need for the user to provide a base_url and model name: `cha -p`

#### Model Autoselection (-sm)

- `cha -sm`
- `cha -sm <MODEL_NAME>`

#### Token Counting (-t) with a File

- `cha -t -f <FILE>`
- Example:
  ```bash
  cha -t -f README.md
  ```

#### Direct “How to” / “Make me” / “Craft me” Questions

These appear frequently with “cha” followed by a question/request referencing programming, shell commands, or general tasks, for example:

- `cha how many seconds is in a day`
- `cha in python how can I save a dict to a json`
- `cha craft me a unix command to find all Cargo.toml`
- `cha make me a simple flask API`

In essence, your unique “cha” CLI usage falls into these main patterns:

- Running “cha” with a direct query.
- Doing code dumps or debug dumps (-code_dump, -c, -d).
- Performing answer searches (-a).
- Feeding in file input (-f).
- Specifying or switching models (-m, -sm).
- Running OCR operations (-ocr).
- Switching platforms (-p).
- Checking token counts (-t).
- Asking a broad variety of how-to / make-me requests directly after “cha …”.

Both commands support and accept additional parameters. Here is the help page for reference:

```bash
usage: cha [-h] [-pt] [-m MODEL] [-sm] [-f FILE] [-t] [-ocr OCR] [-p [PLATFORM]] [-d [CODE_DUMP]] [-a] [string ...]

Chat with an OpenAI GPT model.

positional arguments:
  string                Non-interactive mode, feed a string into the model

options:
  -h, --help            show this help message and exit
  -pt, --print_title    Print initial title during interactive mode
  -m MODEL, --model MODEL
                        Model to use for chatting
  -sm, --select_model   Select one model from OpenAI's supported models
  -f FILE, --file FILE  Filepath to file that will be sent to the model (text only)
  -t, --token_count     Count tokens for the input file or string
  -ocr OCR, --ocr OCR   Given a file path, print the content of that file as text though Cha's main file loading logic
  -p [PLATFORM], --platform [PLATFORM]
                        Use a different provider, set this like this: "<base_url>|<api_key_env_name>", or use as a flag
                        with "-p" for True
  -d [CODE_DUMP], --code_dump [CODE_DUMP]
                        Do a full code dump into one file in your current directory
  -a, -as, --answer_search
                        Run answer search
```

## Development

For those interested in contributing or experimenting with Cha:

1. **Install Cha in Editable Mode**:

   ```bash
   pip install -e .
   ```

2. **Develop and Test**: Modify the source code and test changes using `cha`.

3. **(optional) Load your Custom Configuration**: Use the `CHA_PYTHON_CUSTOM_CONFIG_PATH` environment variable to point to a custom `config.py` file that overrides default global variables. Set it using `export CHA_PYTHON_CUSTOM_CONFIG_PATH="/path/to/your/config.py"`. Ensure your defined variables are in uppercase.

4. **(Optional) Update Cha's "setup.py" or run system checks to ensure proper functionality**: Run the following command in the same directory as Cha's code:

   ```bash
   python3 maintain.py
   ```

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

## Contributing

Any contribution is welcomed! Please feel free to submit issues or pull requests for any bugs or features.

## License

Cha is licensed under the MIT License. See [LICENSE](./LICENSE) for more details.
