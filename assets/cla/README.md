# Cla

## Overview

Cla is an open-source command-line tool for interacting with Anthropic’s Claude models. It provides an easy-to-use terminal-based interface for chatting with powerful AI models. Learn more about Anthropic's API though their [docs](https://docs.anthropic.com/en/docs/welcome). It allows you to chat with Anthropic Claude models in both interactive and non-interactive modes. It supports multi-line input, file-based input, and dynamically scrapes Anthropic docs to provide a list of available models. Cla also leverages Cha's core functionality, including its robust scraper library and utilities, to enhance its operations.

## Features

- CLI chat interface for direct interaction
- Interactive & non-interactive modes (string or file input)
- Multi-line input mode for complex prompts
- Dynamic model selection by scraping Anthropic’s documentation
- Chat history management with options to clear or save

## Installation

Simply run the installation script to install all dependencies:

```bash
bash install.sh
```

## Usage

Start an interactive session with the default model:

```bash
python3 main.py
```

To select a different model:

```bash
python3 main.py --select_model
```

For non-interactive mode (sending a string):

```bash
python3 main.py "Hello, Claude!"
```

To send a text file to the model:

```bash
python3 main.py --file path/to/your/file.txt
```
