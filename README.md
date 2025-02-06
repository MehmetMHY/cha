# Cha

![image](https://github.com/user-attachments/assets/03eff35f-1489-49a8-9e3f-23723f1b1c1c)

## Overview

Cha is an open-source command-line tool that simplifies interactions with AI models from OpenAI. It allows users to efficiently engage with powerful language models directly from their terminal, enhancing development workflows. Check out the detailed demo [here](https://youtu.be/7zG8iFZjKtM?si=sOenMYNUb7XSWAsi).

## Vision

Cha is a simple, lightweight CLI tool that provides access to powerful AI models directly from the terminal. Think of it like Vim versus Emacs: Cha focuses on simplicity and versatility, delivering essential functionality without overwhelming complexity. It's designed to fit seamlessly into your workflow, helping to reduce the need for developers to leave their terminals, making AI access and general knowledge querying straightforward and efficient.

## Features

- **CLI Chat Interface**: Communicate with OpenAI's models via commands `cha`.
- **Interactive & Non-interactive Modes**: Interact with models via chat interface, command-line arguments, or file input.
- **Multi-line Input Mode**: Simplifies complex input directly into the CLI.
- **Text-Editor Input Mode**: Use your system's terminal-based text editor instead of Python's `input()`, allowing easier input of complex and long prompts.
- **Web and YouTube Scraping**: Extract YouTube video transcripts, web PDFs, and general web content.
- **Image Generation**: Generate custom images using OpenAI's image models.
- **Answer Search**: Simple implementation of an Answer-Search engine similar to Perplexity AI's solution.
- **Estimate Tokens**: Option to estimate the token count for a file, string, or piped content.
- **Support for Multiple File Types**: Supports a variety of file types for input, including PDF, DOCX, XLSX, and common image formats, enabling seamless integration and processing of different kinds of content.
- **Platform Flexibility**: Seamlessly switch between different AI platform providers offering OpenAI-compatible APIs using the `-p` or `--platform` argument.

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

### Configuration

1. **API Key Setup**: Cha just requires a OpenAI API which you can grab [HERE](https://platform.openai.com/api-keys)

2. **Setup your .env file**: Create a `.env` file in the root directory and add your keys

   ```bash
   export OPENAI_API_KEY="YOUR_OPENAI_API_KEY"
   ```

3. **Apply the environment variables**

   ```bash
   source .env
   ```

### Usage

To start using **cha**, run the following simple command:

```bash
cha
```

Both commands support and accept additional parameters. Here are all of their respected help page for reference:

```bash
usage: cha [-h] [-pt] [-a] [-m MODEL] [-sm] [-f FILE] [-i [IMAGE]] [-t] [-p [PLATFORM]] [string ...]

Chat with an OpenAI GPT model.

positional arguments:
  string                Non-interactive mode, feed a string into the model

options:
  -h, --help            show this help message and exit
  -pt, --print_title    Print initial title during interactive mode
  -a, -as, --answer_search
                        Run answer search
  -m MODEL, --model MODEL
                        Model to use for chatting
  -sm, --select_model   Select one model from OpenAI's supported models
  -f FILE, --file FILE  Filepath to file that will be sent to the model (text only)
  -i [IMAGE], --image [IMAGE]
                        Generate image (flag only) or print the metadata for generated images (provide filepath)
  -t, --token_count     Count tokens for the input file or string
  -p [PLATFORM], --platform [PLATFORM]
                        Use a different provider, set this like this: "<base_url>|<api_key_env_name>"
```

## Different Platforms - OpenAI Compatibility Platforms/APIs

Cha now supports the option to switch between different AI platforms by using the `--platform` argument. This feature allows you to interoperate with other services offering OpenAI-compatible APIs.

### Example Command

Use the `platform` argument to specify the provider's API and the corresponding environment variable for the API key.

Example call:

```bash
export TOGETHER_API_KEY="..."

cha -p "https://api.together.xyz/v1|TOGETHER_API_KEY" -m "deepseek-ai/DeepSeek-V3"
```

### Possible Platforms

#### Perplexity AI API

- API's Documentation: [Perplexity AI Docs](https://docs.perplexity.ai/guides/getting-started)
- Supported Models: [Perplexity AI Models](https://docs.perplexity.ai/guides/model-cards)

#### DeepSeek API

- API's Documentation: [DeepSeek API Docs](https://api-docs.deepseek.com/)
- Supported Models: [DeepSeek Models](https://api-docs.deepseek.com/quick_start/pricing)

#### Groq API

- API's Documentation: [Groq API Docs](https://console.groq.com/docs/openai)
- Supported Models: [Groq Models](https://console.groq.com/docs/models)

#### Together AI API

- API's Documentation: [Together AI Docs](https://docs.together.ai/docs/openai-api-compatibility)
- Supported Models:
  - [Together AI Models - 1](https://docs.together.ai/reference/models-1)
  - [Together AI Models](https://www.together.ai/models)

## Development

For those interested in contributing or experimenting with Cha:

1. **Install Cha in Editable Mode**:

   ```bash
   pip install -e .
   ```

2. **Develop and Test**: Modify the source code and test changes using `cha`.

3. **(optional) Load your Custom Configuration**: Use the `CHA_PYTHON_CUSTOM_CONFIG_PATH` environment variable to point to a custom `config.py` file that overrides default global variables. Set it using `export CHA_PYTHON_CUSTOM_CONFIG_PATH="/path/to/your/config.py"`. Make sure your defined variables is all uppercase.

4. **(optional) Update Cha's "setup.py" File**: To do this, be in the same directory where Cha's code is located (this repo). Then, run the command listed below

   ```bash
   python3 update.py
   ```

## Contributing

Any contribution is always welcomed! Please feel free to submit issues or pull requests for any bugs or features.

## License

Cha is licensed under the MIT License. See [LICENSE](./LICENSE) for more details.
