#!/usr/bin/env bash

set -euo pipefail

# configuration
CHA_HOME="$HOME/.cha"
VENV_DIR="$CHA_HOME/venv"
REPO_URL="https://github.com/MehmetMHY/cha.git"

# helper functions
log() {
	echo -e "\033[96m$1\033[0m"
}

error() {
	echo -e "\033[91mERROR: $1\033[0m" >&2
	exit 1
}

# prerequisite checks
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

	log "Checking system dependencies for $os"

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

	log "The following dependencies are missing: ${missing_deps[*]}"
	echo -n -e "\033[93mDo you want to install them? (y/N): \033[0m"
	read -r response
	if [[ ! "$response" =~ ^[Yy]$ ]]; then
		error "Installation aborted. Please install dependencies manually."
	fi

	case "$os" in
	"macos")
		if ! command -v brew >/dev/null 2>&1; then
			error "Homebrew is required on macOS to install dependencies. Install from https://brew.sh/"
		fi
		for dep in "${missing_deps[@]}"; do
			log "Installing $dep with Homebrew..."
			brew install "$dep"
		done
		;;
	"linux")
		if command -v sudo >/dev/null 2>&1; then
			if command -v apt-get >/dev/null 2>&1; then
				sudo apt-get update -qq
				for dep in "${missing_deps[@]}"; do
					log "Installing $dep with apt-get..."
					sudo apt-get install -y "$dep"
				done
			elif command -v pacman >/dev/null 2>&1; then
				for dep in "${missing_deps[@]}"; do
					log "Installing $dep with pacman..."
					sudo pacman -Sy --noconfirm "$dep"
				done
			elif command -v dnf >/dev/null 2>&1; then
				for dep in "${missing_deps[@]}"; do
					log "Installing $dep with dnf..."
					sudo dnf install -y "$dep"
				done
			elif command -v yum >/dev/null 2>&1; then
				for dep in "${missing_deps[@]}"; do
					log "Installing $dep with yum..."
					sudo yum install -y "$dep"
				done
			else
				error "Unsupported package manager. Please install manually: ${missing_deps[*]}"
			fi
		else
			error "sudo is required to install dependencies on Linux. Please install it first."
		fi
		;;
	esac
}

# core installation logic
create_venv() {
	log "Creating/updating Python virtual environment in $VENV_DIR"
	mkdir -p "$CHA_HOME" || error "Failed to create directory $CHA_HOME"

	if [[ -d "$VENV_DIR" ]]; then
		echo -e "\033[93mAn existing Cha installation was found.\033[0m"
		echo -n -e "\033[93mWould you like to perform a fresh install (y) or update the current installation (N)? [y/N]: \033[0m"
		read -r response
		if [[ "$response" =~ ^[Yy]$ ]]; then
			log "Removing existing virtual environment..."
			rm -rf "$VENV_DIR"
		else
			# if venv exists, update it.
			log "Updating existing installation..."

			log "Upgrading pip, setuptools, and wheel..."
			"$VENV_DIR/bin/python" -m pip install --upgrade pip setuptools wheel --quiet || error "Failed to upgrade pip components"

			log "Updating cha package..."
			"$VENV_DIR/bin/pip" install --upgrade . --quiet || error "Failed to update cha package"
			return
		fi
	fi

	python3 -m venv "$VENV_DIR" || error "Failed to create virtual environment"

	log "Purging pip cache..."
	"$VENV_DIR/bin/python" -m pip cache purge >/dev/null 2>&1 || log "Could not purge pip cache, continuing..."

	log "Upgrading pip, setuptools, and wheel..."
	"$VENV_DIR/bin/python" -m pip install --upgrade pip setuptools wheel --quiet || error "Failed to upgrade pip components"

	log "Installing cha package..."
	"$VENV_DIR/bin/pip" install . --quiet || error "Failed to install cha package"
}

run_checkup() {
	echo -n -e "\033[93mDo you want to run the dependency checkup? [Y/n]: \033[0m"
	read -r response
	if [[ "$response" =~ ^[Nn]$ ]]; then
		log "Skipping dependency checkup"
		return
	fi
	log "Running dependency checkup..."
	if [ ! -f "assets/dev_tools/checkup.py" ]; then
		error "checkup.py script not found. Installation might be corrupted."
	fi
	"$VENV_DIR/bin/python" assets/dev_tools/checkup.py || error "Dependency checkup failed"
}

create_symlink() {
	log "Creating symlink for 'cha' in /usr/local/bin"
	local target_dir="/usr/local/bin"
	local symlink_path="$target_dir/cha"
	local source_path="$VENV_DIR/bin/cha"

	if [[ ! -d "$target_dir" ]]; then
		log "Directory $target_dir does not exist. Creating it with sudo."
		if command -v sudo >/dev/null 2>&1; then
			sudo mkdir -p "$target_dir"
		else
			error "sudo is required to create $target_dir. Please create it manually and re-run."
		fi
		if [[ $? -ne 0 ]]; then
			error "Failed to create $target_dir. Please create it manually and re-run the script."
		fi
	fi

	if [[ -w "$target_dir" ]]; then
		ln -sf "$source_path" "$symlink_path"
		log "Symlink created: $symlink_path -> $source_path"
	else
		log "Attempting to create symlink with sudo..."
		if command -v sudo >/dev/null 2>&1; then
			sudo ln -sf "$source_path" "$symlink_path"
		else
			error "sudo is required to create symlink in $target_dir. Please create it manually."
		fi
		if [[ $? -ne 0 ]]; then
			error "Failed to create symlink. Please try creating it manually: sudo ln -sf \"$source_path\" \"$symlink_path\""
		fi
		log "Symlink created with sudo: $symlink_path -> $source_path"
	fi
}

print_success() {
	echo
	echo -e "\033[92m🎉 Cha installation/update complete!\033[0m"
	echo
	echo -e "Cha and its virtual environment are installed in: \033[90m$CHA_HOME\033[0m"
	echo -e "A symlink has been created at /usr/local/bin/cha, so you can run 'cha' from anywhere."
	echo
	echo -e "\033[93mImportant:\033[0m"
	echo -e "Make sure '/usr/local/bin' is in your \$PATH."
	echo -e "You can check by running: \033[90mecho \$PATH\033[0m"
	echo -e "You may need to restart your terminal session for changes to take effect."
	echo
	echo -e "To get started, simply type:"
	echo -e "  \033[96mcha\033[0m"
	echo
	echo -e "If you installed via curl/wget, the cloned repository has been removed."
}

check_git_and_pull() {
	if ! command -v git >/dev/null 2>&1; then
		error "Git is required to run the installation script. Please install it first."
	fi
	log "Pulling latest changes from git..."
	git pull || error "Failed to pull latest changes from git"
}

_install_cha_from_repo() {
	log "Starting Cha installation process from local repository..."
	check_python
	install_dependencies
	create_venv
	run_checkup
	create_symlink
	print_success
}

# main execution
main() {
	# check if running from a local git repo of 'cha'
	if [ -f "setup.py" ] && [ -d "cha" ] && [ -d ".git" ]; then
		log "Running installer from existing local repository."
		check_git_and_pull
		_install_cha_from_repo
	else
		log "Welcome to the Cha installer!"
		log "This script will download and install Cha on your system."

		if ! command -v git >/dev/null 2>&1; then
			error "Git is required to run this installer. Please install it first."
		fi

		local temp_dir
		temp_dir=$(mktemp -d 2>/dev/null || mktemp -d -t 'cha-install')
		# shellcheck disable=SC2064
		trap "log 'Cleaning up temporary files...'; rm -rf '$temp_dir'" EXIT

		log "Cloning Cha repository into a temporary directory..."
		git clone --depth 1 "$REPO_URL" "$temp_dir" || error "Failed to clone the repository."

		cd "$temp_dir" || error "Failed to enter the temporary directory."

		_install_cha_from_repo
	fi
}

main "$@"
