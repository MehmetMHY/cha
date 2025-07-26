#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CHA_HOME="$HOME/.cha"
VENV_DIR="$CHA_HOME/venv"

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

	if ! python3 -m pip --version >/dev/null 2>&1; then
		error "pip is required but not available"
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

	if [[ "$os" == "linux" ]] && ! command -v espeak-ng >/dev/null 2>&1; then
		missing_deps+=("espeak-ng")
	fi

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
			apt-get update -qq
			for dep in "${missing_deps[@]}"; do
				log "Installing $dep"
				apt-get install -y "$dep"
			done
		elif command -v pacman >/dev/null 2>&1; then
			for dep in "${missing_deps[@]}"; do
				log "Installing $dep"
				pacman -Sy --noconfirm "$dep"
			done
		elif command -v dnf >/dev/null 2>&1; then
			for dep in "${missing_deps[@]}"; do
				log "Installing $dep"
				dnf install -y "$dep"
			done
		elif command -v yum >/dev/null 2>&1; then
			for dep in "${missing_deps[@]}"; do
				log "Installing $dep"
				yum install -y "$dep"
			done
		else
			error "Unsupported package manager. Please install manually: ${missing_deps[*]}"
		fi
		;;
	esac
}

create_venv() {
	log "Creating Python virtual environment in $VENV_DIR"
	mkdir -p "$CHA_HOME" || error "Failed to create directory $CHA_HOME"

	if [[ -d "$VENV_DIR" ]]; then
		echo -e "\033[93mExisting venv/ found: $VENV_DIR\033[0m"
		echo -n -e "\033[91mRemove it and continue? (y/N): \033[0m"
		read -r response
		if [[ "$response" =~ ^[Yy]$ ]]; then
			log "Removing existing virtual environment"
			rm -rf "$VENV_DIR"
		else
			log "Keeping existing virtual environment"
		fi
	fi

	python3 -m venv "$VENV_DIR" || error "Failed to create virtual environment"

	log "Purging pip cache"
	"$VENV_DIR/bin/python" -m pip cache purge || error "Failed to purge pip cache"

	log "Upgrading pip, setuptools, and wheel"
	"$VENV_DIR/bin/python" -m pip install --upgrade pip setuptools wheel --quiet || error "Failed to upgrade pip components"

	log "Installing cha"
	"$VENV_DIR/bin/pip" install -e . --quiet || error "Failed to install cha package"
}

run_checkup() {
	log "Running dependency check"
	cd "$SCRIPT_DIR" || error "Failed to change to script directory"
	"$VENV_DIR/bin/python" assets/utils/checkup.py || error "Dependency check failed"
}

create_symlink() {
	log "Creating symlink for 'cha' in /usr/local/bin"
	local target_dir="/usr/local/bin"
	local symlink_path="$target_dir/cha"
	local source_path="$VENV_DIR/bin/cha"

	if [[ ! -d "$target_dir" ]]; then
		log "Directory $target_dir does not exist. Creating it with sudo."
		sudo mkdir -p "$target_dir"
		if [[ $? -ne 0 ]]; then
			error "Failed to create $target_dir. Please create it manually and re-run the script."
		fi
	fi

	if [[ -w "$target_dir" ]]; then
		ln -sf "$source_path" "$symlink_path"
		log "Symlink created: $symlink_path -> $source_path"
	else
		log "Attempting to create symlink with sudo..."
		sudo ln -sf "$source_path" "$symlink_path"
		if [[ $? -ne 0 ]]; then
			error "Failed to create symlink. Please try creating it manually: sudo ln -sf \"$source_path\" \"$symlink_path\""
		fi
		log "Symlink created with sudo: $symlink_path -> $source_path"
	fi
}

print_success() {
	echo
	echo -e "\033[92m🎉 Cha installation complete!\033[0m"
	echo
	echo -e "Cha and its virtual environment are installed in: \033[90m$CHA_HOME\033[0m"
	echo -e "A symlink has been created at /usr/local/bin/cha, so you can run 'cha' from anywhere."
	echo
	echo -e "\033[93mImportant:\033[0m"
	echo -e "Make sure '/usr/local/bin' is in your \$PATH."
	echo -e "You can check by running: \033[90mecho \$PATH\033[0m"
	echo
	echo -e "To get started, simply type:"
	echo -e "  \033[96mcha\033[0m"
	echo
	echo -e "You can now safely remove the cloned repository directory if you wish."
}

check_git_and_pull() {
	if ! command -v git >/dev/null 2>&1; then
		error "Git is required to run the installation script. Please install it first."
	fi
	log "Pulling latest changes from git..."
	git pull || error "Failed to pull latest changes from git"
}

main() {
	log "Starting Cha installation"
	log "Script directory: $SCRIPT_DIR"

	check_git_and_pull
	check_python
	install_dependencies
	create_venv
	run_checkup
	create_symlink
	print_success
}

main "$@"
