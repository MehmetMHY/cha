#########################[CHA_CONFIGS]#########################

# get OpenAI API key: https://platform.openai.com/api-keys
export OPENAI_API_KEY=""

# (optional) get GROQ API key: https://console.groq.com/keys
export GROQ_API_KEY=""

# (optional) get Anthropic API key: https://docs.anthropic.com/en/api/getting-started
export ANTHROPIC_API_KEY=""

# cha's github repo: https://github.com/MehmetMHY/cha
# run Cha in interactive mode (chat interface) without arguments or in non-interactive mode (processing one or multiple string arguments) if an argument is provided
chatgpt() {
	# set a default OpenAI model
	#   - model list: https://platform.openai.com/docs/models
	DEFAULT_MODEL="gpt-4o"

	if [[ "$1" == "-f" && -n "$2" ]]; then
		cha -m $DEFAULT_MODEL -f "$2"
	elif [ $# -eq 0 ]; then
		cha --model $DEFAULT_MODEL
	else
		cha -m $DEFAULT_MODEL -s "$*"
	fi
}

#########################[CHA_CONFIGS]#########################
