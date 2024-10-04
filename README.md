<p align="center">
    <img width="300" src="./assets/logo.png">
</p>

## About

A simple CLI chat tool designed for easy interaction with OpenAI's models. It also allows you to easily interact with Anthropic's Claude models and Groq's API.

## Features

- Basic CLI chat interface with OpenAI's LLM models.
- Web scraping capability for provided links (supports both HTTP & JavaScript scraping).
- YouTube scraping functionality for extracting video transcripts.
  - The YouTube scraper either scrapes transcripts or downloads the video's audio and converts it to text using OpenAI's Whisper model though the Groq API.
- Multi-line support for easy copying and pasting into the CLI.
- Ability to generate images using OpenAI's image models.
  - Uses CLImage to display images directly in the terminal.
- Supports both interactive and non-interactive chat modes.
- Basic support for other models on different platforms:
  - Anthropic's Claude models via the `cla` command.
  - Groq's API through the `grq` command.

## Demo

<div align="center">

[![Demo Video](./assets/thumbnail.png)](https://www.youtube.com/watch?v=zRnMu6OHNtU)

</div>

## How To Set Up?

#### 1. Install `cha`

Clone this repository, navigate to its directory, and run the following command to install or upgrade `cha`:

```bash
pip3 install --upgrade .
```

#### 2. Configure API Keys

1. Create a `.env` file in the root directory.

2. Obtain your API keys:

   - OpenAI API key: [Get it here](https://platform.openai.com/api-keys)
   - Anthropic API key: [Get it here](https://www.anthropic.com/) (for `cla` command)
   - Groq API key: [Get it here](https://console.groq.com/keys) (for `grq` command)

3. Add your keys to the `.env` file, using this format:

   ```bash
   # Replace YOUR_KEY_HERE with your respective API keys
   export OPENAI_API_KEY="YOUR_KEY_HERE"
   export ANTHROPIC_API_KEY="YOUR_KEY_HERE"
   export GROQ_API_KEY="YOUR_KEY_HERE"
   ```

4. To activate the environment variables, run:

   ```bash
   source .env
   ```

#### 3. Run `cha`, `cla`, or `grq`

To start the tool, execute one of the following:

```bash
# talk with OpenAI's models
cha

# talk with Anthropic's models
cla

# talk with Groq's supported models
grq
```

#### 4. (Optional) Using my configuration of `cha`

If you would like, you can use my configuration of `cha`. To view my configuration, check out the `cha.sh` file. To use it, add the API key(s) and copy the content from the `cha.sh` file to your shell's config file:

```bash
# zsh
cat cha.sh >> $HOME/.zshrc

# bash
cat cha.sh >> $HOME/.bashrc
```

Then, run my configuration of `cha`:

```bash
chatgpt
```

#### 5. Now you're now ready to go!

## Develop Mode

#### 1. For developing Cha, you can do the following. Install `cha` in editable mode so that pip points to the source files of the cloned code:

```bash
pip install -e .
```

#### 2. Make changes to the code, then run `cha`, `cla`, or `grq` to try out your changes

#### 3. If you add a new dependency, you will have to do step 1 again

## Other Notes

- To see and/or change hard-coded config variables/logic in Cha, checkout the `config.py` file.

## Credits

- [OpenAI Documentation](https://platform.openai.com/docs/overview)
- [Anthropic Documentation](https://docs.anthropic.com/)
- [Groq Documentation](https://console.groq.com/docs/quickstart)
- [Ollama's CLI](https://ollama.com/)
- [ChatGPT (GPT-4)](https://chat.openai.com/)
- [Claude 3.5 Sonnet](https://claude.ai/chats)
