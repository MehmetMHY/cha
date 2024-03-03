<p align="center">
  <img width="300" src="./assets/logo.png">
</p>

## About

A simple CLI chat tool to easily interface with OpenAI's LLM models

## Demo:

<div align="center">

[![Demo Video](./assets/thumbnail.png)](https://www.youtube.com/watch?v=qOOzjTdmg7w)

*click the image to view the YouTube video or click here: https://www.youtube.com/watch?v=qOOzjTdmg7w*

</div>

## How To Set Up?

### 1. Install cha

Run the following command to install or upgrade `cha`:

```bash
pip3 install --upgrade .
```

### 2. Configure API Key

1. Create a `.env` file in the root directory.

2. Get your OpenAI API key [HERE](https://platform.openai.com/api-keys).

3. Add your OpenAI API key to the `.env` file, following this format:

```env
# Replace YOUR_KEY_HERE with your actual API key
export OPENAI_API_KEY="YOUR_KEY_HERE"
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

### 5. Optional, setup alias/command for cha

You can create a useful alias/command to simplify the use of `cha`. Add this to your `.zshrc` or `.bashrc`. For example, here is a command I have in my `.zshrc`:

```bash
chatgpt () {
    DEFAULT_MODEL="gpt-4-turbo-preview"
    
    # source OpenAI API key env variable
    source /Users/mehmet/.custom/.env

    if [ $# -eq 0 ]; then
        cha --model $DEFAULT_MODEL
    else
        cha "$@"
    fi

    unset OPENAI_API_KEY
}
```

Now you should be all set!

## Credits

- OpenAI Documentation
- ChatGPT (GPT-4)
- Ollama's CLI tool

