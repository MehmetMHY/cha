# Cha - OpenAI Chat CLI Tool

## About

A simple chat CLI tool I made to talk with OpenAI LLM models

## How To Set Up?

1. Get the code for this and go to it's directory
2. Setup python3 environment:
    ```
    python3 -m venv env
    source env/bin/activate
    ```
3. Install python package requirements:
    ```
    pip3 install -r requirements.txt
    ```
4. Close python environment:
    ```
    deactivate
    ```
5. Get and add your OpenAI key to the .keys file, then source it:
    ```
    # the key should look like this:
    #   export OPENAI_API_KEY=""

    source .env
    ```
6. Setup Ollama: https://ollama.ai/
    - Install it and following each step
    - After you have it installed, open a terminal and run this:
        ```
        ollama
        ```
    - If the above command works, you are good!
7. Run the main script:
    ```
    python3 main.py
    ```
8. (optional) If you want to make this into a command, do the following:
   1. Add the following to your .bashrc or .zshrc file:
        ```
        # NOTE: you set the <root_path> value
        cha () {
            source <root_path>/cha/.env
            <root_path>/cha/env/bin/python3 <root_path>/cha/main.py $1 $2
            unset OPENAI_API_KEY
        }
        ```
    2. Start a new terminal or re-source your .bashrc or .zshrc file
    3. Use the command:
        ```
        cha
        ```

## Credits

- OpenAI Documentations
- ChatGPT (GPT-4)

