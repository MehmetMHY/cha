#!/usr/bin/env bash

set -euo pipefail

# install system dependencies
install_pkg() {
	if command -v brew >/dev/null 2>&1; then
		brew install "$1"
	elif command -v apt-get >/dev/null 2>&1; then
		sudo apt-get update
		sudo apt-get install -y "$1"
	elif command -v pacman >/dev/null 2>&1; then
		sudo pacman -Sy --noconfirm "$1"
	fi
}

# install ffmpeg if not already installed
if ! command -v ffmpeg >/dev/null 2>&1; then
	install_pkg ffmpeg
fi

# install fzf if not already installed
if ! command -v fzf >/dev/null 2>&1; then
	install_pkg fzf
fi

# create virtual environment in the current directory
echo "Creating Python virtual environment in ./venv"

# create virtual environment
python3 -m venv ./venv

# activate virtual environment and install
source "./venv/bin/activate"
python -m pip install --upgrade pip
pip install -e .

# check for dependencies by running Cha's own dependency checker
printf "\n\n"
echo "Checking Dependencies:"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
python assets/checkup.py

# print final important message to the user for final steps
printf "\n\n"
echo "Cha installation is complete!"
echo
echo "ImportantNotes:"
echo "   - If you use 'pyenv', you may need to run 'pyenv rehash'."
echo "   - The 'checkup.py' script just ran to verify your setup. If you saw any '✗', please address them."
echo "   - To add custom tools, activate the venv ('source venv/bin/activate') before installing their dependencies."
echo
echo "To use 'cha' in your CURRENT session, run this command:"
echo "   export PATH=\"${SCRIPT_DIR}/venv/bin:\$PATH\""
echo
echo "To use 'cha' PERMANENTLY, add that line to your shell profile (~/.bashrc, ~/.zshrc)."
echo
echo "You can also run it directly anytime:"
echo "   ${SCRIPT_DIR}/venv/bin/cha"
