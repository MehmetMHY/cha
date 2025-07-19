#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/venv"

if [[ -z "$SCRIPT_DIR" ]]; then
	echo -e "\033[91mERROR: Could not determine script directory\033[0m" >&2
	exit 1
fi

log() {
	echo -e "\033[96m$1\033[0m"
}

error() {
	echo -e "\033[91mERROR: $1\033[0m" >&2
	exit 1
}

check_python() {
	if ! command -v python3 >/dev/null 2>&1; then
		error "Python 3 is required but not installed"
	fi

	local python_version
	python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
	if ! python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)"; then
		error "Python 3.9+ is required (found $python_version)"
	fi
}

detect_os() {
	if [[ "$OSTYPE" == "darwin"* ]]; then
		echo "macos"
	elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
		echo "linux"
	else
		error "Unsupported operating system: $OSTYPE"
	fi
}

install_dependencies() {
	local os
	os=$(detect_os)

	log "Installing system dependencies for $os"

	local deps=("ffmpeg" "fzf" "bat" "ripgrep" "netcat")
	local missing_deps=()

	for dep in "${deps[@]}"; do
		local cmd="$dep"
		[[ "$dep" == "ripgrep" ]] && cmd="rg"
		[[ "$dep" == "netcat" ]] && cmd="nc"

		if ! command -v "$cmd" >/dev/null 2>&1; then
			missing_deps+=("$dep")
		fi
	done

	if [[ ${#missing_deps[@]} -eq 0 ]]; then
		log "All dependencies already installed"
		return
	fi

	case "$os" in
	"macos")
		if ! command -v brew >/dev/null 2>&1; then
			error "Homebrew is required on macOS. Install from https://brew.sh/"
		fi
		for dep in "${missing_deps[@]}"; do
			log "Installing $dep"
			brew install "$dep"
		done
		;;
	"linux")
		if command -v apt-get >/dev/null 2>&1; then
			sudo apt-get update -qq
			for dep in "${missing_deps[@]}"; do
				log "Installing $dep"
				sudo apt-get install -y "$dep"
			done
		elif command -v pacman >/dev/null 2>&1; then
			for dep in "${missing_deps[@]}"; do
				log "Installing $dep"
				sudo pacman -Sy --noconfirm "$dep"
			done
		elif command -v dnf >/dev/null 2>&1; then
			for dep in "${missing_deps[@]}"; do
				log "Installing $dep"
				sudo dnf install -y "$dep"
			done
		else
			error "Unsupported package manager. Please install manually: ${missing_deps[*]}"
		fi
		;;
	esac
}

create_venv() {
	log "Creating Python virtual environment"

	if [[ -d "$VENV_DIR" ]]; then
		echo
		echo -e "\033[93mExisting venv/ found: $VENV_DIR\033[0m"
		echo -n -e "\033[91mRemove it and continue? (y/N): \033[0m"
		read -r response
		if [[ "$response" =~ ^[Yy]$ ]]; then
			log "Removing existing virtual environment"
			rm -rf "$VENV_DIR"
		else
			log "Keeping existing virtual environment"
		fi
		echo
	fi

	python3 -m venv "$VENV_DIR"
	source "$VENV_DIR/bin/activate"

	log "Upgrading pip"
	python -m pip install --upgrade pip --quiet

	log "Installing cha"
	pip install -e . --quiet
}

run_checkup() {
	log "Running dependency check"
	echo
	cd "$SCRIPT_DIR"
	python assets/checkup.py
}

print_success() {
	echo
	echo -e "\033[92m🎉 Cha installation complete!\033[0m"
	echo
	echo -e "\033[93mNext steps:\033[0m"
	echo -e "  \033[96m1.\033[0m Add to PATH: \033[90mexport PATH=\"$VENV_DIR/bin:\$PATH\"\033[0m"
	echo -e "  \033[96m2.\033[0m Add to shell profile for permanent use (~/.bashrc, ~/.zshrc)"
	echo -e "  \033[96m3.\033[0m Or run directly: \033[90m$VENV_DIR/bin/cha\033[0m"
	echo
	echo -e "\033[93mFor current session:\033[0m"
	echo -e "  \033[90mexport PATH=\"$VENV_DIR/bin:\$PATH\"\033[0m"
}

main() {
	log "Starting Cha installation"
	log "Script directory: $SCRIPT_DIR"

	check_python
	install_dependencies
	create_venv
	run_checkup
	print_success
}

main "$@"
