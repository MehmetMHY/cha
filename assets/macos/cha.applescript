on run
	set shellLine to "open -n -a kitty --args bash -lc " & ¬
		quote & "[ -f \"$HOME/.custom/.env\" ] && source \"$HOME/.custom/.env\"; " & ¬
		"$HOME/.pyenv/shims/cha || echo \"cha failed\"; exec bash" & quote
	
	do shell script shellLine
end run
