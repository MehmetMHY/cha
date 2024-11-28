# Cha

![image](https://github.com/user-attachments/assets/03eff35f-1489-49a8-9e3f-23723f1b1c1c)

## Overview

Cha is an open-source command-line tool that simplifies interactions with AI models from OpenAI. It allows users to efficiently engage with powerful language models directly from their terminal, enhancing development workflows. Check out the detailed demo [here](https://youtu.be/7zG8iFZjKtM?si=sOenMYNUb7XSWAsi).

## Vision

Cha is a simple, lightweight CLI tool that provides access to powerful AI models directly from the terminal. Think of it like Vim versus Emacs: Cha focuses on simplicity and versatility, delivering essential functionality without overwhelming complexity. It's designed to fit seamlessly into your workflow, helping to reduce the need for developers to leave their terminals, making AI access and general knowledge querying straightforward and efficient.

## Features

- **CLI Chat Interface**: Communicate with OpenAI's models via commands `cha`
- **Interactive & Non-interactive Modes**: Interact with models via chat interface, command-line arguments, or file input.
- **Multi-line Input Mode**: Simplifies complex input directly into the CLI.
- **Text-Editor Input Mode**: Use your system's terminal based text editor instead of Python's `input()`, allowing easier input of complex and long prompts.
- **Web and YouTube Scraping**: Extract YouTube video transcripts, web PDFs, and general web content.
- **Image Generation**: Generate custom images using OpenAI's image models.
- **Answer Search**: Simple implementation of an Answer-Search engine similar to Perplexity AI's solution
- **Estimate Tokens**: Option to estimate the token count for a file, string, or piped content.
- **Back to Command Line**: Temporarily exit to the system shell from within the chat interface, execute shell commands, and return to the chat without closing the application.
- **Support for Multiple File Types**: Supports a variety of file types for input, including PDF, DOCX, XLSX, and common image formats, enabling seamless integration and processing of different kinds of content.

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
usage: cha [-h] [-pt] [-as] [-m MODEL] [-sm] [-f FILE] [-i [IMAGE]] [-t]
           [string ...]

Chat with an OpenAI GPT model.

positional arguments:
  string                Non-interactive mode, feed a string into the
                        model

options:
  -h, --help            show this help message and exit
  -pt, --print_title    Print initial title during interactive mode
  -as, --answer_search  Run answer search
  -m MODEL, --model MODEL
                        Model to use for chatting
  -sm, --select_model   Select one model from OpenAI's supported models
  -f FILE, --file FILE  Filepath to file that will be sent to the model
                        (text only)
  -i [IMAGE], --image [IMAGE]
                        Generate image (flag only) or print the metadata
                        for generated images (provide filepath)
  -t, --token_count     Count tokens for the input file or string
```

### Docker

Cha can be run in Docker and accessed through the browser. This is great if you want to access Cha from the browser and/or avoid installing the dependencies for Cha by running it in a sandbox. To setup and run the Docker version of Cha, checkout [this](./docker/) section of the repo.

## Development

For those interested in contributing or experimenting with Cha:

1. **Install in Editable Mode**:

   ```bash
   pip install -e .
   ```

2. **Develop and Test**: Modify the source code and test changes using `cha`.

3. **(optional) Load your Custom Configuration**: Use the `CHA_PYTHON_CUSTOM_CONFIG_PATH` environment variable to point to a custom `config.py` file that overrides default global variables. Set it using `export CHA_PYTHON_CUSTOM_CONFIG_PATH="/path/to/your/config.py"`. Make sure your defined variables is all uppercase.

## Contributing

Any contribution is always welcomed! Please feel free to submit issues or pull requests for any bugs or features.

## License

Cha is licensed under the MIT License. See [LICENSE](./LICENSE) for more details.

## Acknowledgments

Cha is inspired and/or made possible thanks to:

- [OpenAI Documentation](https://platform.openai.com/docs/overview)
- [ChatBlade](https://github.com/npiv/chatblade)
- [ChatGPT by OpenAI (GPT-4)](https://chat.openai.com/)
- [Claude 3.5 Sonnet](https://claude.ai/chats)
