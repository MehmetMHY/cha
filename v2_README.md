# Cha

## Overview

**Cha** is an open-source command-line AI assistant that streamlines interactions with OpenAI's models directly from your terminal. It enables developers and power users to chat with powerful language models, run searches with AI, via AI models, and even fetch content from the web, all without leaving the command line. Designed to enhance productivity, Cha integrates AI assistance into everyday development workflows in a simple and efficient manner.

## Vision

Cha is a simple, lightweight CLI tool that provides access to powerful AI models directly from the terminal. Think of it like **Vim versus Emacs**: Cha focuses on simplicity and versatility, delivering essential functionality without overwhelming complexity. It's designed to fit seamlessly into your workflow, reducing the need to leave the terminal and making AI-driven knowledge querying straightforward and efficient.

## Feature Comparison Table

Cha offers a rich set of features aimed at making AI usage convenient from the CLI. The table below summarizes key functionalities:

| **Feature**                    | **Description**                                                                                                            |
| ------------------------------ | -------------------------------------------------------------------------------------------------------------------------- |
| **CLI Chat Interface**         | Chat with OpenAI's language models directly in your terminal with a natural dialogue flow.                                 |
| **Interactive & Batch Modes**  | Use Cha in interactive chat sessions or one-off query mode (via command arguments or piped input).                         |
| **Multi-line Prompt Input**    | Easily compose multi-line prompts directly in the CLI for complex or formatted queries.                                    |
| **Text-Editor Integration**    | Open your default terminal text editor to write extensive prompts, then send to the model.                                 |
| **Web & YouTube Scraping**     | Provide a URL (webpage or YouTube video) and Cha will retrieve page text or video transcripts for context.                 |
| **Answer Search Engine**       | Perform an online search for your query and get an AI-crafted answer with relevant information (similar to Perplexity AI). |
| **Token Count Estimation**     | Calculate and display the token count of a given text, file, or piped input without making a model query.                  |
| **Multiple File Type Support** | Accept various file formats (PDF, DOCX, XLSX, images, etc.) as input; Cha will extract and use their content.              |
| **Model Switching**            | Easily switch between different OpenAI models (e.g. gpt-4o, o1, o3-mini) during a conversation or for a single query.      |
| **Multi-Platform Support**     | Point Cha to OpenAI-compatible APIs from other providers (e.g. Azure, Together AI) using the `--platform` option.          |
| **Code Dump Utility**          | Dump an entire codebase (a file or directory) into a single text file to use as context or for analysis.                   |

## Installation

Cha can be installed via pip or directly from the source. **Prerequisites:** Python 3.9.2 or higher, and an OpenAI API key.

### Install via PyPI (pip)

The easiest way to install Cha is from PyPI using pip:

```bash
pip install git+https://github.com/MehmetMHY/cha.git
```

After installation, ensure the `cha` command is accessible by running `cha --help` to see the usage message.

### Install from Source (GitHub)

If you prefer to use the latest development version or contribute to Cha, you can install from source:

1. **Clone the repository**:

   ```bash
   git clone https://github.com/MehmetMHY/cha.git
   cd cha
   ```

2. **Install the package** in your environment (use `--upgrade` to ensure latest dependencies):

   ```bash
   pip install --upgrade .
   ```

   _Alternatively_, for development install in editable mode:

   ```bash
   pip install -e .
   ```

3. **Configure API Key**: Cha requires an OpenAI API key to function. See the **Configuration** section below for setup.

#### Configuration

After installation, set up your OpenAI credentials:

- **Obtain an API Key**: Sign up for an OpenAI account and get your API key from the OpenAI dashboard.
- **Set the API Key**: Define the environment variable `OPENAI_API_KEY` with your key. You can add it to a `.env` file in the project directory or export it in your shell:
  ```bash
  export OPENAI_API_KEY="YOUR_OPENAI_API_KEY"
  ```
- If you use a `.env` file, load it into your shell with:
  ```bash
  source .env
  ```
  On Windows, set the environment variable in the Command Prompt or PowerShell:
  ```powershell
  $env:OPENAI_API_KEY="YOUR_OPENAI_API_KEY"
  ```

Cha is now ready to use once the `OPENAI_API_KEY` is configured.

## Usage & Examples

Using Cha is straightforward. You can either launch an interactive chat session or run single-prompt queries directly. Below are examples of common usage scenarios:

### Interactive Chat Session

Start an interactive session to have a back-and-forth conversation with the AI (similar to a chatbot in your terminal):

```bash
$ cha
```

This drops you into an interactive prompt where you can type messages and receive model responses continuously. For example:

```
> Hello, Cha!
AI: Hello! How can I assist you today?
> Give a quick summary of Einstein's theory of relativity.
AI: Albert Einstein's theory of relativity encompasses two interrelated theories... [response continues]
```

Exit the session by pressing `Ctrl+D` or `Ctrl+C` when you're done.

### One-Off Prompt (Non-Interactive)

If you prefer not to enter an interactive session, you can send a single query and get an immediate answer. Simply provide your query as an argument:

```bash
$ cha "How many moons does Jupiter have?"
```

Cha will print the model's answer and exit. This mode is useful for quick questions or when scripting Cha as part of other shell commands.

### Using a File as Input

Cha can take file content as part of the prompt. Use the `-f` option with a file path or URL to have Cha read that content:

```bash
$ cha -f notes.txt "Summarize the key points from the attached notes."
```

In this example, Cha will read the text from `notes.txt` and then answer the prompt using that content as context. This works with various file types, for instance, you can provide a PDF, Word document, or an image:

```bash
$ cha -f report.pdf "Provide a concise summary of this report."
$ cha -f diagram.png "Explain the text in this diagram image."
```

Cha will automatically extract text from supported documents or perform OCR on images to use the text in its response.

You can also input a URL directly:

```bash
$ cha -f "https://en.wikipedia.org/wiki/OpenAI" "What does this page say about GPT-4?"
```

Cha will fetch the webpage content and answer based on that information. For YouTube links, it will retrieve the video transcript:

```bash
$ cha -f "https://www.youtube.com/watch?v=dQw4w9WgXcQ" "Give me a summary of this video."
```

### Answer Search Mode

For factual questions that might require up-to-date information, Cha offers an _Answer Search_ mode. Use the `-a` flag to let Cha perform a web search and then answer your question:

```bash
$ cha -a
```

Cha will search the web for relevant information and provide an answer (with reference data) through the language model. This mode is similar to using an AI search engine and is useful for questions beyond the AI model's trained knowledge cutoff.

### Switching Models

By default, Cha uses a predefined OpenAI model (e.g., gpt-4o). You can specify a different model with the `-m` option:

```bash
$ cha -m gpt-4o "Explain the significance of the number 42 in literature."
```

This will run your prompt using the GPT-4 model (if you have access to it via your API key). You can use any model identifier supported by the OpenAI API. In an interactive session, you can even switch models between turns by specifying `-m` for a query if needed.

### Dumping Code Context

If you want the AI to analyze code or multiple files, use the **code dump** feature. The `-d` (`--code_dump`) option will gather code from your project:

```bash
# dump the current directory's code into a file for analysis
$ cha -d
```

This command creates a single text file (in the current directory) containing all code files, which can then be used as context in the conversation. You might use this in combination with a prompt:

```bash
$ cha -d
Using directory: /Users/mehmet/SandBox/git/GitHub/MehmetMHY/cha
Select directories to exclude (comma-separated numbers) or press Enter to skip:
  1. cha/
> 1
Select files to exclude (comma-separated numbers) or press Enter to skip:
  1. .gitignore
  2. LICENSE
  3. README.md
  4. setup.py
  5. update.py
>
Token Count: ~5962
Saved codedump to: code_dump_1740511574.txt
$ cha -f code_dump_1740511574.txt "Review the code above and identify any bugs."
```

Cha will dump the code and then ask the model to analyze it. You can also specify a particular directory or file with `-d path/to/dir` to dump specific content.

## Advanced Features

Cha includes several advanced capabilities and options that empower power-users to get the most out of the tool:

- **Flexible Prompt Entry**: In interactive mode, Cha supports multi-line input. This means you can press `Enter` without sending the prompt immediately, allowing you to compose a question or piece of code over multiple lines. When ready, submit the prompt (by sending an empty line or a specific key stroke as instructed in the CLI) and Cha will process the entire input. For extremely long prompts, Cha can also invoke your default terminal editor (as set by `$EDITOR`) so you can comfortably write and edit before sending.

- **AI Platform Switching**: Using the `--platform` (`-p`) option, you can direct Cha to use alternative AI platforms that implement OpenAI-compatible APIs. For example, Cha can work with Azure's OpenAI service or community-run endpoints. Running `cha -p` by itself will present an interactive menu of configured third-party platforms (defined in Cha's `config.py`). To skip the menu, you can provide the platform details directly. For instance:

  ```bash
  # Example: use Together AI platform with a specific model
  export TOGETHER_API_KEY="YOUR_API_KEY"
  cha -p "https://api.together.xyz/v1|TOGETHER_API_KEY" -m together-ai/awesome-model
  ```

  In this way, Cha integrates with multiple backends while using the same interface. (Refer to the project's `THIRD_PARTY_PLATFORMS` configuration for platforms supported out-of-the-box.)

- **JavaScript-enabled Web Scraping**: Cha's web scraping can handle not just static HTML but also dynamic content. Under the hood, it can execute JavaScript when needed to retrieve content from modern websites. This means you can feed Cha pages that require JavaScript to render (for example, single-page applications or content behind scripts), and Cha will still capture the meaningful text. This happens automatically when you use `-f` with a URL; no additional flags are required.

- **Token Counting Utility**: If you need to know how large a prompt or file is before sending it to the model, Cha offers a token estimation tool. Using the `-t` (`--token_count`) option with a string or file will output the estimated number of tokens:

  ```bash
  $ cha -t -f draft_article.txt
  ```

  This will print the token count for the content of `draft_article.txt` so you can gauge model usage and ensure you stay within model limits. No API call is made for this operation.

- **Custom Configuration**: Advanced users can override global settings of Cha by using a custom configuration file. If you set the environment variable `CHA_PYTHON_CUSTOM_CONFIG_PATH` to point to a Python file, Cha will import it to override default configurations. In this custom config, you can adjust default model names, temperature, system prompts, or other advanced settings. (Make sure any variable you override is defined in all-caps in your config file.) This provides a way to tailor Cha's behavior without modifying the source code directly.

## Common Issues & Troubleshooting

While Cha is designed to be user-friendly, you may encounter certain issues. Below are some common problems and how to address them:

- **`cha: command not found`** - After installation, if the `cha` command isn't recognized, ensure that your Python's bin directory is in your system PATH. You might need to reopen your terminal or run the install command with the correct Python/pip. For example, use `pip3 install cha` if your system defaults to Python 2 for `pip`. You can also check the installation by running `python3 -m cha --help` as a fallback.

- **OpenAI API key not set or invalid** - If you run Cha and it immediately exits or returns an authentication error, it likely means the API key is missing or incorrect. Double-check that `OPENAI_API_KEY` is set in your environment (use `echo $OPENAI_API_KEY` on Linux/Mac or `$env:OPENAI_API_KEY` in PowerShell to verify). Ensure there are no extra quotes or spaces in the value. If you have multiple OpenAI keys (or multiple platforms configured), confirm you're using the right environment variable name for the platform in use (e.g., Azure may require `AZURE_OPENAI_KEY` in the config).

- **Model not found or model access error** - If you specify a model with `-m` and receive an error that the model is not available, it could be either a typo in the model name or your API key not having access to that model. Verify the model name (for example, use `gpt-4` not `GPT4`) and ensure your OpenAI account has access (some models like GPT-4 require invitation or certain access). You can list available models with the OpenAI API or use `cha -sm` to select from supported models interactively.

- **Large file or prompt issues** - When using a very large file or extremely long prompt, you might hit token limits or performance issues. OpenAI's models have a context size limit (e.g., ~128,000 tokens for GPT-4o and o1 models). If the AI does not return an answer or truncates it, the input may be too long. In such cases, consider summarizing your input, splitting the content into smaller chunks, or using a model with a larger context window. The token count feature (`-t`) can help estimate size before sending. Additionally, very large code dumps or file inputs might take some time to process; be patient or reduce the scope if possible. Note that while GPT-4o and o1 models have larger context windows, they may still have limitations on output tokens (e.g., up to 32,768 for o1-preview and 65,536 for o1-mini).

- **Web scraping failures** - If you use `-f` with a URL and Cha fails to retrieve content (or you get an error message about scraping), the target website might be inaccessible or blocking automated scraping. Ensure you have an internet connection. For some PDF URLs or unusual websites, Cha might not fetch content if it encounters unexpected formats or requires special access. If a YouTube transcript cannot be retrieved (for very new or restricted videos), you may need to wait or ensure the video has captions available. As a workaround, you can manually obtain the content (e.g., download a PDF or copy text) and then provide it to Cha as a file.

- **Rate limits or slow responses** - The OpenAI API enforces rate limits and can sometimes be slow, especially for complex queries or when the service is under heavy load. If Cha's responses are very delayed or you get rate-limit errors, you might need to throttle your usage. This can involve inserting pauses between queries or upgrading your API plan. Cha itself does not implement request throttling, so the user should be mindful of not sending too many requests in a short time. If you hit errors, wait a moment and try again. For persistent issues, check OpenAI's status page or your account usage dashboard.

If your issue isn't listed above, check the [GitHub Issues page](https://github.com/MehmetMHY/cha/issues) for any similar reports or to open a new issue. The community and maintainers can help diagnose and fix new problems.

## Contribution & Development

Contributions to Cha are welcome and encouraged! Whether you want to add new features, fix bugs, or improve documentation, please follow these guidelines to get started:

### Setting Up a Development Environment

1. **Fork and Clone**: Start by forking the Cha repository on GitHub, then clone your fork:
   ```bash
   git clone https://github.com/<your-username>/cha.git
   cd cha
   ```
2. **Install in Editable Mode**: It's recommended to install Cha in _editable_ (`dev`) mode for development:
   ```bash
   pip install -e .
   ```
   This will link the `cha` command to your cloned source, so any changes you make to the code will be reflected when you run `cha`.
3. **Run Cha for Testing**: After installation, test that everything works by running `cha --help` or a simple prompt. Ensure you have your `OPENAI_API_KEY` set as described earlier.
4. _(Optional)_ **Custom Config for Development**: You can create a `config.py` in the project directory to override settings (such as using a mock API key or a test model) and point the environment variable `CHA_PYTHON_CUSTOM_CONFIG_PATH` to it. This helps in development if you need custom behavior or to avoid using real tokens during testing.

### Contribution Guidelines

- **Issue Tracker**: If you find a bug or have an idea for enhancement, open an issue on GitHub. This allows discussion and feedback before significant work is done.
- **Pull Requests**: Pull requests are welcome. When developing, create a new branch for your feature or fix (e.g., `feature/add-new-mode` or `fix/typo-readme`). Submit a PR to the `main` branch of the original repository when ready. Ensure your PR description clearly states the problem and solution/improvements.
- **Coding Style**: Try to follow the coding conventions used in the project. For Python code, that means adhering to PEP8 style where possible (consistent naming, spacing, etc.). If adding new dependencies, discuss in an issue first to ensure they are necessary.
- **Testing**: Before submitting a pull request, test your changes thoroughly. If the project includes automated tests (check for any `tests/` directory or instructions), run them. If not, at least verify common use cases manually (for example, ensure that basic chat, file input, and any modified feature still work as expected). Adding new unit tests for new functionality is highly appreciated.
- **Documentation**: If you add a feature or change existing behavior, update the README or any relevant documentation. Aim for clarity and conciseness in docs. This ensures users can immediately benefit from your contribution.
- **Discuss First**: For major feature proposals or sweeping changes, it's best to open an issue or discussion to get feedback from the maintainer(s) and community. This can save time and align contributions with the project's roadmap and vision.

By contributing to Cha, you agree to license your contributions under the same MIT License that covers the project.

## License

This project is licensed under the **MIT License**. You are free to use, modify, and distribute Cha in both personal and commercial projects. See the [LICENSE](https://github.com/MehmetMHY/cha/blob/main/LICENSE) file for the full license text.
