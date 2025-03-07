# NOTE: the goal of this script is to easily update the dependencies in Cha's SETUP file
# NOTE: make sure to run this script in the root directory of the Cha project

from pathlib import Path
import subprocess
import requests
import shutil
import time
import sys
import os
import re

try:
    from cha import config
    LOADED_CHA_PKGS = True
except:
    LOADED_CHA_PKGS = False

def safe_input(starting_text):
    try:
        return input(starting_text)
    except (KeyboardInterrupt, EOFError):
        print()
        sys.exit(1)


def checkup():
    # check if required environment variables are loaded
    try:
        from cha import config
        for platform in config.THIRD_PARTY_PLATFORMS:
            env_name = str(config.THIRD_PARTY_PLATFORMS[platform].get("env_name"))
            if env_name in os.environ:
                print(f"✓ (OPTIONAL) {env_name} is set")
                continue
            print(f"! (OPTIONAL) {env_name} variable is missing")

        if "OPENAI_API_KEY" in os.environ:
            print("✓ OPENAI_API_KEY is set")
        else:
            print("✗ OPENAI_API_KEY variable is missing")
    except:
        pass

    # check if the local ollama client is running or not
    try:
        from cha import config

        if "ollama" not in config.THIRD_PARTY_PLATFORMS:
            raise Exception("Ollama not included in platform config")
        url = config.THIRD_PARTY_PLATFORMS["ollama"]["models"]["url"]
        response = requests.get(url, timeout=3)
        if response.status_code == 200:
            print("✓ Ollama is running locally")
        else:
            print("! Ollama is not running locally")
    except:
        pass

    # check if ffmpeg is installed or not
    try:
        subprocess.run(
            ["ffmpeg", "-version"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        print("✓ ffmpeg seems to be installed")

    except (subprocess.CalledProcessError, FileNotFoundError):
        print("✗ ffmpeg is not installed, please install it: https://ffmpeg.org/")

    # check if whisper model is installed and working
    try:
        from cha import config

        whisper_model_weight_file_path = (
            f"{str(Path.home())}/.cache/whisper/{config.DEFAULT_WHISPER_MODEL_NAME}.pt"
        )
        if os.path.isfile(whisper_model_weight_file_path) == False:
            import whisper

            whisper.load_model(config.DEFAULT_WHISPER_MODEL_NAME)
        print(f"✓ Whisper model weight exists at {whisper_model_weight_file_path}")

    except Exception as e:
        print(f"✗ failed to find Whisper model {e}")

    # check to make sure at least one of the supported Terminal IDEs are installed
    supported_terminal_ide_installed = False
    for editor in config.SUPPORTED_TERMINAL_IDES:
        if shutil.which(editor):
            supported_terminal_ide_installed = True
            break
    if supported_terminal_ide_installed:
        print(f"✓ Supported Terminal IDE is installed")
    else:
        print(
            f"✗ None of the supported terminal IDE(s) are installed: {config.SUPPORTED_TERMINAL_IDES}"
        )

    # check if git is installed or not
    try:
        subprocess.run(
            ["git", "--version"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        print("✓ Git found (for code-dump feature)")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("✗ Git not installed or not on PATH")

    # check if yt-dlp is installed, correctly, or not
    if shutil.which("yt-dlp"):
        print("✓ yt-dlp found (for YouTube transcripts)")
    else:
        print("✗ yt-dlp not installed or not on PATH")


def update_setup():
    # path to setup file
    PYTHON_SETUP_FILE_PATH = None
    for i in range(4):
        setup_file_path = "/".join(
            os.path.dirname(os.path.abspath(__file__)).split("/")[:-(i)] + ["setup.py"]
        )
        if os.path.isfile(setup_file_path):
            PYTHON_SETUP_FILE_PATH = setup_file_path
            break

    if PYTHON_SETUP_FILE_PATH is None:
        print("Failed to load 'setup.py' file(s) because it does not exist!")
        sys.exit(1)

    # confirm the loaded setup file path is correct
    print(f"Found 'setup.py' at:\n{PYTHON_SETUP_FILE_PATH}")
    confirm_input = safe_input(f"Continue with this path (Y/n)? ")
    if confirm_input.lower() in ["n", "no"]:
        PYTHON_SETUP_FILE_PATH = safe_input(
            "Please manually input the path to 'setup.py': "
        ).strip()
        if not os.path.isfile(PYTHON_SETUP_FILE_PATH):
            print(f"The file path '{PYTHON_SETUP_FILE_PATH}' does not exist!")
            sys.exit(1)

    # read the current setup file
    with open(PYTHON_SETUP_FILE_PATH, "r") as f:
        content = f.read()

    # get and update version
    version_match = re.search(r'version="([^"]*)"', content)
    if version_match:
        current_version = version_match.group(1)
        print(f"Current version: {current_version}")
        new_version = safe_input("Enter new version: ").strip()
        if len(new_version) == 0 or "." not in new_version:
            new_version = current_version
        content = content.replace(
            f'version="{current_version}"', f'version="{new_version}"'
        )

    # find all dependencies
    deps = re.findall(r'"([^"]+)==([^"]+)"', content)

    print("Scanning dependencies...")

    # update each dependency
    changed_count = 0
    for package, current_version in deps:
        try:
            # get latest version by running the pip CLI command
            result = subprocess.run(
                ["pip", "index", "versions", package],
                capture_output=True,
                text=True,
                check=True,
            )

            # extract latest version
            for line in result.stdout.split("\n"):
                if "Available versions:" in line:
                    latest_version = line.split(":")[1].strip().split(",")[0].strip()
                    if latest_version != current_version:
                        print(
                            f"Updating {package}: {current_version} -> {latest_version}"
                        )
                        content = content.replace(
                            f'"{package}=={current_version}"',
                            f'"{package}=={latest_version}"',
                        )
                        changed_count += 1
                    break

        except subprocess.CalledProcessError:
            print(f"Failed to get version for {package}, skipping...")
            continue

    # write updated content
    with open(PYTHON_SETUP_FILE_PATH, "w") as f:
        f.write(content)
    print(f"Updated setup file!")

    print(f"A total of {changed_count} package versions got changed!")

    # (optional) reinstall Cha
    user_input = safe_input(f"Do you like to reinstall Cha (Y/n)? ")
    if user_input.lower() in ["y", "yes"]:
        user_input = safe_input('Install without "-e" option (Y/n)? ')
        if user_input.lower() in ["y", "yes"]:
            print('> Installing Cha WITHOUT "-e" Option!')
            os.system("pip3 install .")
        else:
            print('> Installing Cha WITH "-e" Option!')
            os.system("pip3 install -e .")


if __name__ == "__main__":
    user_choice = safe_input("Run CHECKUP [1] or UPGRADE [2]? ").strip().lower()
    if user_choice in ["2", "u", "upgrade", "update", "up", "setup"]:
        update_setup()
    else:
        # NOTE: default to checkup function call to make it easier for the user(s)
        checkup()
