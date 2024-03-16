
#########################[CHA_CONFIGS]#########################

# get OpenAI API key: https://platform.openai.com/api-keys
export OPENAI_API_KEY=""

# get Brave API key: https://api.search.brave.com/app/keys
export BRAVE_API_KEY=""

# run Cha in interactive mode (chat interface) without arguments or in non-interactive mode (processing one or multiple string arguments) if an argument is provided
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

