# Cha

## Overview

Cha is an open-source command-line tool that simplifies interactions with AI models from OpenAI and Anthropic. It allows users to efficiently engage with powerful language models directly from their terminal, enhancing development workflows.

[Watch the demo](https://www.youtube.com/watch?v=zRnMu6OHNtU) to see Cha in action!

## Features

- **CLI Chat Interface**: Communicate with OpenAI's and Anthropic's models via commands `cha` and `cla`
- **Web and YouTube Scraping**: Extract YouTube video transcripts, web pdfs, and general web content.
- **Multi-line Input Mode**: Simplifies complex input directly into the CLI.
- **Interactive and Non-interactive Modes**: Tailor your experience.
- **Image Generation**: Generate custom images using OpenAI's image models.
- **Estimate Tokens**: Option to estimate the token count for a file, string, or piped content.

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

1. **API Keys Setup**: Grab your API keys from the following links

   - [OpenAI API key](https://platform.openai.com/api-keys)
   - [Anthropic API key](https://www.anthropic.com/)

2. **Setup your .env file**: Create a `.env` file in the root directory and add your keys

   ```bash
   export OPENAI_API_KEY="YOUR_OPENAI_API_KEY"
   export ANTHROPIC_API_KEY="YOUR_ANTHROPIC_API_KEY"
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

To start using **cla**, run the following simple command:

```bash
cla
```

Both commands support and accept additional parameters. Here are all of their respected help page for reference:

```bash
usage: cha [-h] [-pt] [-m MODEL] [-sm] [-f FILE] [-igmd IG_METADATA] [string ...]

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
  -igmd IG_METADATA, --ig_metadata IG_METADATA
                        Print the meta data for generated images
```

```bash
usage: cla [-h] [-m MODEL] [-sm] [-f FILE] [-pt] [string ...]

Chat with an Anthropic Claude model.

positional arguments:
  string                Non-interactive mode, feed a string into the model

options:
  -h, --help            show this help message and exit
  -m MODEL, --model MODEL
                        Model to use for chatting
  -sm, --select_model   Select one model from Anthropic's supported models
  -f FILE, --file FILE  Filepath to file that will be sent to the model (text only)
  -pt, --print_title    Print initial title during interactive mode
```

## Development

For those interested in contributing or experimenting with Cha:

1. **Install in Editable Mode**:
   ```bash
   pip install -e .
   ```
2. **Develop and Test**: Modify the source code and test changes using `cha` or `cla`.

3. **(optional) Load your Custom Configuration**: Use the `CHA_PYTHON_CUSTOM_CONFIG_PATH` environment variable to point to a custom `config.py` file that overrides default global variables. Set it using `export CHA_PYTHON_CUSTOM_CONFIG_PATH="/path/to/your/config.py"`. Make sure your defined variables is all uppercase.

## Contributing

Any contribution is always welcomed! Please feel free to submit issues or pull requests for any bugs or features.

## Changelog

For a detailed list of changes, please see the [CHANGELOG.md](./CHANGELOG.md).

## License

Cha is licensed under the MIT License. See [LICENSE](./LICENSE) for more details.

## Acknowledgments

Cha is inspired and/or made possible thanks to:

- [OpenAI Documentation](https://platform.openai.com/docs/overview)
- [Anthropic Documentation](https://docs.anthropic.com/)
- [ChatBlade](https://github.com/npiv/chatblade)
- [ChatGPT by OpenAI (GPT-4)](https://chat.openai.com/)
- [Claude 3.5 Sonnet](https://claude.ai/chats)
