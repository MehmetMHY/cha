<p align="center">
    <img width="300" src="./assets/logo.png">
</p>

## About

A simple CLI chat tool designed for easy interaction with OpenAI's models.

## Alternatives

If you want to use Anthropic's models in the CLI, check out [Cla](https://github.com/MehmetMHY/cla)!

## Features

- Basic CLI chat interface with OpenAI’s LLM models.
- Web scraping capability for provided links (supports JavaScript scraping).
- YouTube scraping functionality for extracting video transcripts.
- Answer-Search feature utilizing the Brave API, similar to the Perplexity AI search engine.
    - Click [HERE](https://www.youtube.com/watch?v=pTHk5G6TzH4) to view a demo of the Answer-Search feature.
- Multi-line support for easy copying and pasting into the CLI.
- Ability to generate images using OpenAI's image models.
    - Uses CLImage to display images directly in the terminal.
- Supports both interactive and non-interactive chat modes.
- Stats option that estimates how much you have spent per session.

## Demo

<div align="center">

[![Demo Video](./assets/thumbnail.png)](https://www.youtube.com/watch?v=zRnMu6OHNtU)

*Click the image or visit https://www.youtube.com/watch?v=zRnMu6OHNtU*

</div>

## How To Set Up?

### 1. Install `cha`

Clone this repository, navigate to its directory, and run the following command to install or upgrade `cha`:

```bash
pip3 install --upgrade .
```

### 2. Configure API Key

1. Create a `.env` file in the root directory.

2. Obtain your OpenAI API key [HERE](https://platform.openai.com/api-keys). If you want to use Answer-Search, obtain your Brave API key [HERE](https://brave.com/search/api/).

3. Add your keys to the `.env` file, using this format:

    ```env
    # Replace YOUR_KEY_HERE with your OpenAI API key
    OPENAI_API_KEY="YOUR_KEY_HERE"

    # (Optional) Replace YOUR_KEY_HERE with your Brave API key
    BRAVE_API_KEY="YOUR_KEY_HERE"
    ```

4. To activate the environment variables, run:

```bash
source .env
```

### 3. Run `cha`

To start the tool, execute:

```bash
cha
```

### 4. (Optional) Setup an Alias/Command for `cha`

For easier use of `cha`, consider setting up an alias or command. To add the preferred alias/command for Cha, run the appropriate command for your shell:

```bash
# if using a zsh shell
echo 'alias cha="path/to/cha"' >> $HOME/.zshrc

# if using a bash shell
echo 'alias cha="path/to/cha"' >> $HOME/.bashrc
```

You're now ready to go!

## Develop Mode

For developing Cha, you can do the following:

### 1. Install `cha` in editable mode so that pip points to the source files of the cloned code:

```bash
pip install -e .
```

### 2. Make changes to the code, then run `cha` to try out your changes

### 3. If you add a new dependency, you will have to do step 1 again

## Other Notes

- To see and/or change hard-coded config variables/logic in Cha, checkout the `config.py` file.

## Credits

- [OpenAI Documentation](https://platform.openai.com/docs/introduction)
- [ChatGPT (GPT-4)](https://chat.openai.com/)
- [Ollama's CLI](https://ollama.com/)

