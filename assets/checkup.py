# NOTE: This script acts as a checkup on your system to see which pre-requirements for Cha is installed or not installed

from pathlib import Path
import subprocess
import requests
import shutil
import sys
import os
import re


def passed(text):
    text = f"✓ {text}"
    print(f"\033[92m{text}\033[0m")
    return


def warning(text):
    text = f"! {text}"
    print(f"\033[93m{text}\033[0m")
    return


def failed(text):
    text = f"✗ {text}"
    print(f"\033[91m{text}\033[0m")
    return


def parse_setup_py(file_path="setup.py"):
    with open(file_path, "r") as file:
        content = file.read()

    # find install_requires section
    match = re.search(r"install_requires\s*=\s*\[([^\]]+)\]", content)

    if match:
        # extract package names by removing comments and extra spaces
        packages = [
            pkg.strip().strip("'\"") for pkg in match.group(1).split(",") if pkg.strip()
        ]
        return packages
    return []


def check_installed_packages_with_pip(packages):
    freeze_output = subprocess.check_output(
        [sys.executable, "-m", "pip", "freeze"], text=True
    )

    installed_packages_pip = {
        line.split("==")[0].lower() for line in freeze_output.splitlines()
    }

    installed = []
    missing = []
    for package in packages:
        package_name = package.split("==")[0].lower()
        if package_name in installed_packages_pip:
            installed.append(package)
        else:
            missing.append(package)

    return {"installed": installed, "missing": missing}


def num_of_valid_shells():
    shells = []
    try:
        current_shell = os.environ.get("SHELL")

        try:
            shell_dir = "/etc/shells"
            with open(shell_dir) as f:
                shells = [line.strip() for line in f if line.startswith("/")]
            shells = [x for x in list(set(shells)) if x != current_shell]
        except:
            pass

        try:
            result = subprocess.run(
                ["which", "fish"], capture_output=True, text=True, check=True
            )
            shells.append(result.stdout.strip())
        except subprocess.CalledProcessError:
            pass
    except:
        pass
    return len(shells)


def checkup():
    try:
        response = requests.get("http://www.google.com", timeout=5)
        if response.status_code != 200:
            raise Exception("")
        passed(f"You are connected to the internet!")
    except:
        failed("Not connected to the internet; failing ALL tests")
        return

    try:
        response = requests.get("https://duckduckgo.com", timeout=5)
        if response.status_code != 200:
            raise Exception("")
        passed(f"DuckDuckGo search engine seems to be up and running")
    except requests.exceptions.RequestException as e:
        failed("DuckDuckGo search engine seems to be down")

    try:
        PYTHON_SETUP_FILE_PATH = None
        for i in range(4):
            setup_file_path = "/".join(
                os.path.dirname(os.path.abspath(__file__)).split("/")[:-(i)]
                + ["setup.py"]
            )
            if os.path.isfile(setup_file_path):
                PYTHON_SETUP_FILE_PATH = setup_file_path
                break

        if PYTHON_SETUP_FILE_PATH is None:
            raise Exception(f"Failed to find setup.py file")

        try:
            import pkg_resources
        except ImportError:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", "setuptools"]
            )
            import pkg_resources

        packages = parse_setup_py(PYTHON_SETUP_FILE_PATH)

        result = check_installed_packages_with_pip(packages)
        if len(result["missing"]) > 0:
            failed(f"Cha's dependencies are not installed: {response['missing']}")
        else:
            passed("All of Cha's dependencies are installed")
    except:
        failed("Failed to check if Cha's dependencies are installed or not")

    try:
        import cha

        passed(f"Cha is installed")
    except:
        failed("Cha is NOT installed, skipping all tests!")
        pass

    # check if required environment variables are loaded
    try:
        from cha import config

        for platform in config.THIRD_PARTY_PLATFORMS:
            env_name = str(config.THIRD_PARTY_PLATFORMS[platform].get("env_name"))
            if env_name.lower().strip() == "ollama":
                continue
            if env_name in os.environ:
                passed(f"{env_name} is set")
                continue
            warning(f"{env_name} variable is missing")

        if "OPENAI_API_KEY" in os.environ:
            passed("OPENAI_API_KEY is set")
        else:
            failed("OPENAI_API_KEY variable is missing")
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
            passed("Ollama is running locally")
        else:
            warning("Ollama is not running locally")
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
        passed("Tool ffmpeg seems to be installed")
    except (subprocess.CalledProcessError, FileNotFoundError):
        failed("Tool ffmpeg is not installed, please install it: https://ffmpeg.org/")

    # check if whisper model is installed and working
    try:
        from cha import config
        from faster_whisper import WhisperModel

        model = WhisperModel(
            config.DEFAULT_WHISPER_MODEL_NAME, device="cpu", compute_type="int8"
        )
        del model

        passed(f"Whisper model found")
    except Exception as e:
        failed(f"failed to find Whisper model {e}")

    # check to make sure at least one of the supported Terminal IDEs are installed
    try:
        from cha import config

        test_failed = True
        if any(shutil.which(editor) for editor in config.SUPPORTED_TERMINAL_IDES):
            passed("Supported Terminal IDE is installed")
            test_failed = False
        if test_failed:
            raise Exception(
                f"user's systems has none of the supported terminal text editor(s) installed"
            )
    except:
        failed(f"None of the supported terminal IDE(s) are installed")

    # check if git is installed or not
    try:
        subprocess.run(
            ["git", "--version"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        passed("Git found (for code-dump feature)")
    except (subprocess.CalledProcessError, FileNotFoundError):
        failed("Git not installed or not on PATH")

    # check if yt-dlp is installed, correctly, or not
    if shutil.which("yt-dlp"):
        passed("yt-dlp found (for YouTube transcripts)")
    else:
        failed("yt-dlp not installed or not on PATH")

    # check if fzf is installed or not
    if shutil.which("fzf"):
        passed("fzf found (for fuzzy finding)")
    else:
        failed("fzf not installed or not on PATH")

    valid_shell_count = num_of_valid_shells()
    if valid_shell_count > 0:
        passed("One valid shell was found for Cha's shell mode")
    else:
        failed("Zero valid shells found for Cha's shell mode")

    if os.path.isdir(os.path.join(str(Path.home()), ".cha/")):
        passed("$HOME/.cha/ directly exists!")
    else:
        failed("$HOME/.cha/ directly does NOT exist!")


if __name__ == "__main__":
    try:
        checkup()
    except (KeyboardInterrupt, EOFError):
        print()
