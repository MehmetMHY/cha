# Cha

## Overview

**Cha** is an open-source command-line AI assistant that streamlines interactions with OpenAI (and other OpenAI-compatible) models directly in your terminal. It enables developers and power users to chat with powerful language models, run AI-driven searches, fetch content from the web, and more—**all without leaving the command line**. Designed for productivity, Cha integrates AI assistance into everyday development workflows in a simple yet powerful manner.

## Vision

Cha is a simple, lightweight CLI tool that provides access to powerful AI models directly from the terminal. Think of it like **Vim versus Emacs**: Cha focuses on simplicity and versatility, delivering essential functionality without overwhelming complexity. It’s designed to fit seamlessly into your workflow, reducing the need to leave the terminal and making AI-driven knowledge querying straightforward and efficient.

## Feature Comparison Table

Cha offers a rich set of features aimed at making AI usage convenient from the CLI:

| **Feature**                    | **Description**                                                                                                              |
| ------------------------------ | ---------------------------------------------------------------------------------------------------------------------------- |
| **CLI Chat Interface**         | Chat with OpenAI’s language models directly in your terminal with a natural dialogue flow.                                   |
| **Interactive & Batch Modes**  | Use Cha in interactive chat sessions or one-off query mode (via command arguments or piped input).                           |
| **Multi-line Prompt Input**    | Easily compose multi-line prompts directly in the CLI for complex or formatted queries.                                      |
| **Text-Editor Integration**    | Open your default terminal text editor to write extensive prompts, then send to the model.                                   |
| **Web & YouTube Scraping**     | Provide a URL (webpage or YouTube video) and Cha will retrieve page text or video transcripts for context.                   |
| **Answer Search Engine**       | Perform an online search for your query and get an AI-crafted answer with relevant information.                              |
| **Token Count Estimation**     | Calculate and display the token count of a given text, file, or piped input without making a model query.                    |
| **Multiple File Type Support** | Accept various file formats (PDF, DOCX, XLSX, images, etc.) as input; Cha will extract and use their content.                |
| **Model Switching**            | Easily switch between different OpenAI-style models (e.g., `gpt-4o`, `o3-mini`) during a conversation or for a single query. |
| **Multi-Platform Support**     | Point Cha to OpenAI-compatible APIs from other providers (e.g., Azure, Together AI) using the `--platform` option.           |
| **Code Dump Utility**          | Dump an entire codebase (a file or directory) into a single text file to use as context or for analysis.                     |

## Installation

Cha requires Python 3.9.2 or higher, plus an API key (typically `OPENAI_API_KEY`). You can install Cha either via a GitHub-based pip command (preferred) or by cloning the repository directly.

### Install via Pip (GitHub)

```bash
pip install git+https://github.com/MehmetMHY/cha.git
```

After installation, test with:

```bash
cha --help
```

to see usage instructions.

### Install from Source (GitHub)

If you plan to contribute or want the latest development version:

1. **Clone the repository**:
   ```bash
   git clone https://github.com/MehmetMHY/cha.git
   cd cha
   ```
2. **Install the package**:
   ```bash
   pip install --upgrade .
   ```
   _Alternatively_, in editable mode for local development:
   ```bash
   pip install -e .
   ```
3. **Configure an API Key**:
   - **Obtain an API Key**: For OpenAI, sign up on the [OpenAI dashboard](https://platform.openai.com/) and generate an API key.
   - **Set the Key**: Define `OPENAI_API_KEY` in your environment or `.env` file, e.g.:
     ```bash
     export OPENAI_API_KEY="YOUR_API_KEY"
     ```
     Cha is ready to use once `OPENAI_API_KEY` is set.

## Usage & Examples

Cha supports **interactive** (REPL-style) mode and **non-interactive** (one-off prompt) mode. Below are common usage patterns.

### Interactive Chat Session

Launching Cha without arguments starts a chat-like environment:

```bash
$ cha
```

The default model is configured in `cha/config.py`. In the chat, you’ll see instructions similar to:

```
Chatting With OpenAI's 'gpt-4o' Model
- '!e' or CTRL-C to exit
- '!c' to clear chat history
- '!s' to save chat history
- '!l' to load a file
- '!h' to list all options
- '!a' to run answer search
- '!t' for text-editor input mode
- '!m' for single/multi-line switching
- 'END' to end multi-line mode
- '!sm' switch models
- '!d' to code dump a directory as context
```

Simply type your prompt at the `User:` prompt. For instance:

```
User: Hello, Cha!
AI: Hello! How can I assist you today?

User: Give a quick summary of Einstein's theory of relativity.
AI: Albert Einstein's theory of relativity encompasses two interrelated theories... [response continues]
```

#### Interactive Chat Commands

Within interactive mode, you can use special in-chat commands:

| Command      | Description                                                                               |
| ------------ | ----------------------------------------------------------------------------------------- |
| `!e`         | Exit the session (or press <kbd>Ctrl+C</kbd> / <kbd>Ctrl+D</kbd>).                        |
| `!c`         | Clear chat history (removes all messages for the current session).                        |
| `!s`         | Save the chat history to a JSON file named `cha_<timestamp>.json`.                        |
| `!h`         | Print the list of available commands (help).                                              |
| `!l`         | Load a file from the local directory (Cha will parse text, PDF, or doc).                  |
| `!a`         | Trigger the Answer Search feature (web-based search & summarization).                     |
| `!m` / `END` | Toggle multi-line input mode, letting you compose multi-line queries.                     |
| `!t`         | Open your default terminal text editor (e.g., vim) to compose a multi-line prompt.        |
| `!sm`        | Switch models (Cha will list available models from OpenAI or custom platform).            |
| `!d`         | Perform a code dump of your directory or a specified path, providing the text as context. |

### One-Off Prompt (Non-Interactive)

For quick single queries:

```bash
cha "How many moons does Jupiter have?"
```

Cha prints an immediate response and exits. This is convenient for scripting or short Q&A. If you pass both a string prompt and a file, Cha returns an error (it only accepts one input method at a time in non-interactive mode).

### Using a File as Input

Cha can read and incorporate local files or URLs using the `-f` flag:

```bash
cha -f notes.txt "Summarize the key points."
```

- Accepts PDF, DOCX, XLSX, images (will perform OCR), or standard text.
- You can also pass a URL to fetch its content:
  ```bash
  cha -f "https://en.wikipedia.org/wiki/OpenAI" "What does this page say about GPT-4?"
  ```
- For YouTube links, Cha attempts to retrieve the transcript.
- Output is based on combining the file or webpage content with your additional prompt string.

### Answer Search Mode

Cha implements a minimal “Answer Search” using DuckDuckGo (and optional scraping). Use `-a` or `--answer_search`:

```bash
cha -a
```

Cha will prompt for your question. It then:

1. Generates possible queries to the search engine.
2. Scrapes top results.
3. Summarizes them into an answer with references.

This helps answer questions the local AI model might not fully address due to older training data.

### Switching Models

You can specify a model with `-m`, e.g.:

```bash
cha -m gpt-4o "Explain the significance of the number 42 in literature."
```

Alternatively:

- **Interactively** switch models with `!sm` inside the chat.
- **List Models** from OpenAI with `-sm` on the command line:
  ```bash
  cha -sm
  ```
  Cha will display available models, letting you pick from the list.

### Dumping Code Context

Cha’s `--code_dump` (or `-d`) feature gathers code or text files from your current directory (respecting `.gitignore`) and packages them as a single text file or direct conversation context. For instance:

```bash
cha -d
```

- Prompts you to exclude directories or files interactively.
- Concatenates all remaining text files into one large file (named something like `code_dump_1740511574.txt`).
- You can then feed that file to Cha for analysis or Q&A:
  ```bash
  cha -f code_dump_1740511574.txt "Review the code above and identify any bugs."
  ```

### Token Counting Utility

Use `-t` (`--token_count`) to estimate how many tokens your input consumes without making a model call:

```bash
cha -t -f draft_article.txt
```

Or:

```bash
echo "Hello world from pipe" | cha -t
```

Cha prints the total token count so you can gauge if your prompt might exceed model limits.

### Additional CLI Flags

Here’s a summary of `cha`’s key command-line flags (from the main CLI logic):

| Flag / Argument             | Description                                                                                                                                |
| --------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| `-pt, --print_title`        | Prints an initial banner in interactive mode, listing key commands and usage tips.                                                         |
| `-a, -as, --answer_search`  | Runs the **Answer Search** functionality, prompting you for a question and performing an online search before summarizing results.         |
| `-m, --model MODEL`         | Specifies which AI model to use (e.g., `gpt-4o`, `o3-mini`). Defaults to the config’s `CHA_DEFAULT_MODEL`.                                 |
| `-sm, --select_model`       | Interactively select from OpenAI’s (or platform’s) available models.                                                                       |
| `-f, --file FILE`           | Send the contents of a specified file/URL to the model (supports text, PDF, DOCX, images with OCR, etc.).                                  |
| `string ...`                | Provide a single-prompt query without starting interactive mode.                                                                           |
| `-t, --token_count`         | Estimate token usage for a file/string/pipe, printing the result and exiting.                                                              |
| `-ocr, --ocr FILE`          | Perform an OCR-like extraction on an image, returning recognized text.                                                                     |
| `-p, --platform [PLATFORM]` | Switch to a different provider base URL & API key. If used alone, an interactive menu of configured platforms is shown (from `config.py`). |
| `-d, --code_dump [DIR]`     | Dumps code from the current (or specified) directory into a single text file for usage or analysis.                                        |

## Advanced Features

- **Multi-line Input**: In interactive mode, type `!m` to enter multi-line input. Your typed lines won’t be sent until you type `END` or switch modes. This is handy for large/complex queries.
- **Text-Editor Input**: Type `!t` to open your default terminal editor (e.g., `vim`). Save and close to send the entire content as the prompt.
- **Scraping Logic & Prompts**: Cha identifies URLs in your typed prompt. If it detects them, it’ll ask if you want to scrape. If yes, it fetches the content, merges it into your prompt, and sends it to the model. Useful for instant context from a web article or PDF link.
- **Model Context Handling**: Some models (like `o1`) do not accept system prompts. Cha detects this and omits the default system prompt internally. The rest of the logic remains the same.
- **Platform Switching**: The `--platform` or `-p` argument can change the base URL and API key name. This is experimental but useful if you want to connect to, say, an internal deployment or third-party that follows OpenAI’s API specification. Example:
  ```bash
  cha -p "https://api.together.xyz/v1|TOGETHER_API_KEY"
  ```
- **Help & Debug**: Running `cha --help` lists all recognized arguments. Errors or debug messages typically appear in red if something goes wrong. For instance, if a file doesn’t exist or the model can’t be loaded.

## Common Issues & Troubleshooting

- **`cha: command not found`**  
  Ensure your Python’s script install path is in your `PATH`. For instance, if you installed with `pip3` but your PATH references only `pip2`, you might see this error. Try `pip3 install` or specify a virtual environment.

- **Missing or Invalid API Key**  
  Cha checks for `OPENAI_API_KEY`. If not found, it exits with a prompt. Confirm by running `echo $OPENAI_API_KEY` (macOS/Linux) or `$env:OPENAI_API_KEY` (Windows). If you have multiple environment variables for other providers, ensure you set them too.

- **Model Not Found**  
  If you specify `-m` with a model you don’t have API access to (or it doesn’t exist), you may get an error. Try `cha -sm` or `openai_client.models.list()` to see available models. Also note that some models require invitation or special access from OpenAI.

- **Long Prompt or Large File**  
  Exceeding the model’s maximum context length can lead to partial or truncated responses. Use `-t` to estimate tokens first, or split your file into smaller chunks. Some advanced GPT-4 variants (like `gpt-4o`) allow up to 128k tokens, but performance may degrade as prompt size grows.

- **Web Scraping Failures**  
  If a URL blocks bots or requires complex JavaScript, Cha might fail to retrieve the content. You can manually copy the text or use alternative scraping. YouTube transcripts also require the video to have captions. If missing, you’ll get an error or an empty transcript.

- **Rate Limits & Performance**  
  OpenAI imposes rate limits. If you get slow responses, try spacing out queries or upgrading your usage plan. Cha itself doesn’t throttle requests, so be mindful of how many times you query in short intervals.

## Contribution & Development

We welcome all contributors! If you’d like to modify, extend, or improve Cha, follow these steps:

1. **Fork & Clone**: Fork [MehmetMHY/cha](https://github.com/MehmetMHY/cha) and clone your fork locally.
2. **Install in Editable Mode**:
   ```bash
   pip install -e .
   ```
   This symlinks the `cha` command to your development source. Changes are reflected in real time.
3. **Custom Config** (Optional): For local dev or testing, set `CHA_PYTHON_CUSTOM_CONFIG_PATH` to a custom Python file to override config constants like default model, max tokens, etc.
4. **Pull Requests**: Branch off `main` for features or fixes. Submit a PR with a clear description of your changes, referencing any open issues.
5. **Testing**: Manually verify chat, scraping, code dump, and so on. If you add a feature, please also update documentation and/or add tests (if a test framework is established in the repo).
6. **Coding Style**: Follow the project’s code patterns. For Python, aim for PEP8. Keep new dependencies minimal and discuss them if possible.

By contributing to Cha, you agree to license your contributions under the same MIT License covering the project.

## License

This project is licensed under the **MIT License**. You are free to use, modify, and distribute Cha in both personal and commercial projects.  
See the [LICENSE](https://github.com/MehmetMHY/cha/blob/main/LICENSE) file for the full text.
