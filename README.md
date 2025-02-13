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
- **Platform Flexibility**: Switch between different AI platform providers offering OpenAI-compatible APIs using the `--platform` argument.
- **Switch Model(s) In A Conversion**: Easily switch between models in a conversation.

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

To start using **cha**, run the following simple command:

```bash
cha
```

Both commands support and accept additional parameters. Here is the help page for reference:

```bash
usage: cha [-h] [-pt] [-a] [-m MODEL] [-sm] [-f FILE] [-i [IMAGE]] [-t] [-ocr OCR] [-p [PLATFORM]] [string ...]

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
  -ocr OCR, --ocr OCR   Given a file path, print the content of that file as text though Cha's main file loading logic
  -p [PLATFORM], --platform [PLATFORM]
                        Use a different provider, set this like this: "<base_url>|<api_key_env_name>", or use as a flag
                        with "-p" for True
```

## Development

For those interested in contributing or experimenting with Cha:

1. **Install Cha in Editable Mode**:

   ```bash
   pip install -e .
   ```

2. **Develop and Test**: Modify the source code and test changes using `cha`.

3. **(optional) Load your Custom Configuration**: Use the `CHA_PYTHON_CUSTOM_CONFIG_PATH` environment variable to point to a custom `config.py` file that overrides default global variables. Set it using `export CHA_PYTHON_CUSTOM_CONFIG_PATH="/path/to/your/config.py"`. Ensure your defined variables are in uppercase.

4. **(optional) Update Cha's "setup.py" File**: Run the following command in the same directory as Cha's code:

   ```bash
   python3 update.py
   ```

## Different Platforms - OpenAI Compatibility Platforms/APIs

Cha now supports switching between different AI platforms using the `--platform` argument. This feature allows interoperability with other services offering OpenAI-compatible APIs.

### Platform Details (February 12, 2025)

#### DeepSeek API

- Base URL: https://api.deepseek.com

- Environment Variable: DEEP_SEEK_API_KEY

- Docs: https://api-docs.deepseek.com/

- Get Models Command: `curl -s --request GET --url https://api.deepseek.com/models --header 'Accept: application/json' --header "Authorization: Bearer $DEEP_SEEK_API_KEY" | jq -r '.data[].id' | sort | uniq`

#### Together.AI API

- Base URL: https://api.together.xyz/v1

- Environment Variable: TOGETHER_API_KEY

- Docs: https://docs.together.ai/docs/introduction

- Get Models Command: `curl -s --request GET --url https://api.together.xyz/v1/models --header 'accept: application/json' --header "authorization: Bearer $TOGETHER_API_KEY" | jq '.[] | select(.type == "chat") | .id' | tr -d '"' | sort | uniq`

#### All Current Options

You can refer to the [config.py](./cha/config.py) file and the `THIRD_PARTY_PLATFORMS` variable to see all the other platforms you can try and/or use.

### Example Command

Manually use a different provider/platform:

```bash
# Get and set the provider's API key env variable
export TOGETHER_API_KEY="..."

# Run cha with a different provider/platform
cha -p "https://api.together.xyz/v1|TOGETHER_API_KEY" -m "deepseek-ai/DeepSeek-V3"
```

Or, refer to the [config.py](./cha/config.py) file and the `THIRD_PARTY_PLATFORMS` variable to figure out what environment variables you need to set, then just run this command the pick what platform and model you want to use:

```bash
cha -p
```

## Contributing

Any contribution is welcomed! Please feel free to submit issues or pull requests for any bugs or features.

## License

Cha is licensed under the MIT License. See [LICENSE](./LICENSE) for more details.
