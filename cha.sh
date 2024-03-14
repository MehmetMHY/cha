
#########################[CHA_CONFIGS]#########################

# get OpenAI API key: https://platform.openai.com/api-keys
export OPENAI_API_KEY=""

# get Brave API key: https://api.search.brave.com/app/keys
export BRAVE_API_KEY=""

"""
For this function/code:
- If no arguments are provided, it will run Cha in interactive mode (chat interface).
- If an argument is provided, it will run Cha in non-interactive mode (send one string or multiple string arguments, for your argument).
"""
chatgpt () {
    # set a default OpenAI model
    #   - model list: https://platform.openai.com/docs/models
    DEFAULT_MODEL="gpt-4-turbo-preview"

    # get OpenAI API key: https://platform.openai.com/api-keys
    export OPENAI_API_KEY=""

    # get Brave API key: https://api.search.brave.com/app/keys
    export BRAVE_API_KEY=""

    if [[ "$1" == "-f" && -n "$2" ]]; then
        cha -m $DEFAULT_MODEL -f "$2"
    elif [ $# -eq 0 ]; then
        cha --model $DEFAULT_MODEL
    else
        cha -m $DEFAULT_MODEL -s "$*"
    fi
}

alias ca="chatgpt"

#########################[CHA_CONFIGS]#########################

