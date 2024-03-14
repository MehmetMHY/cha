<p align="center">
    <img width="300" src="./assets/logo.png">
</p>

## About

A simple CLI chat tool to easily interface with OpenAI's LLM models.

## Features

- Basic CLI chat interface to OpenAI’s LLM models.
- Web scraping for a provided link (supports JavaScript scraping).
- YouTube scraping; scraping the transcript from a video.
- Multi-line support; easily copy and paste new lines into the CLI.
- Generate images using OpenAI's image models.
  - CLImage is used to display the image in the terminal
- Supports interactive and non-interactive mode for chatting.
- Answer-Search, using the Brave API, similar to Perplexity AI's search engine.
  - Click [HERE](https://www.youtube.com/watch?v=pTHk5G6TzH4) to see a demo of Answer-Search

## Demo

<div align="center">

[![Demo Video](./assets/thumbnail.png)](https://www.youtube.com/watch?v=YcfFC1IU_SA)

*Click the image or go to https://www.youtube.com/watch?v=YcfFC1IU_SA*

</div>

## How To Set Up?

### 1. Install cha

Clone this repo, cd into it's directory, and run the following command to install or upgrade `cha`:

```bash
pip3 install --upgrade .
```

### 2. Configure API Key

1. Create a `.env` file in the root directory.

2. Get your OpenAI API key [HERE](https://platform.openai.com/api-keys).

3. Add your keys to the `.env` file, following this format:

   - You can get your OpenAI API key [HERE](https://platform.openai.com/api-keys)
   - If you want to use Answer-Search, you need to grab a Brave API key which you can [HERE](https://brave.com/search/api/)

```env
# Replace YOUR_KEY_HERE with your OpenAI API key
export OPENAI_API_KEY="YOUR_KEY_HERE"

# (optional) replace YOUR_KEY_HERE with your Brave API key for Answer-Search
export BRAVE_API_KEY="YOUR_KEY_HERE"
```

4. Activate the environment variables:

```bash
source .env
```

### 3. Run cha

Execute the main script by running:

```bash
cha
```

### 4. Optional, setup an alias/command for cha

To simplify the use of `cha`, you can create a useful alias/command. Either create your own or add the alias/command I use for Cha. To do this, run the following command (only run one of these commands for your respective shell):

```bash
# if you are using a zsh shell
cat cha.sh >> $HOME/.zshrc

# if you are using a sh or bash shell
cat cha.sh >> $HOME/.bashrc
```

Now you should be all set!

## Credits

- OpenAI Documentation
- ChatGPT (GPT-4)
- Ollama's CLI tool

