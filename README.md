<p align="center">
  <img width="300" src="./assets/logo.png">
</p>

## About

A simple chat CLI tool I made to talk with OpenAI LLM models

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

You can make a cool alias/command to make the use of `cha` easier. You can add this to your `.zshrc` or `.bashrc`. As an example, here is a command I have in my `.zshrc`:

```bash
chatgpt () {
    DEFAULT_MODEL="gpt-4-turbo-preview"

    # source OpenAI API key; the "OPENAI_API_KEY" env variable
    source /Users/mehmet/.custom/.env
    
    # install cha: https://github.com/MehmetMHY/cha
    if [ -n "$1" ]; then
        cha
    else
        cha --model $DEFAULT_MODEL
    fi

    unset OPENAI_API_KEY
}
```

Now you should be all set!

## Credits

- OpenAI Documentations
- ChatGPT (GPT-4)

