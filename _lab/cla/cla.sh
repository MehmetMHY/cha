claude() {
	DEFAULT_MODEL="claude-3-5-sonnet-20240620"

	export ANTHROPIC_API_KEY=""

	if [[ "$1" == "-f" && -n "$2" ]]; then
		cla -m $DEFAULT_MODEL -f "$2"
	elif [ $# -eq 0 ]; then
		cla -tp "false" -m $DEFAULT_MODEL
	else
		cla -m $DEFAULT_MODEL -s "$*"
	fi

	unset ANTHROPIC_API_KEY
}
