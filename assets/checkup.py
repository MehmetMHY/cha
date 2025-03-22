from pathlib import Path
import subprocess
import requests
import shutil
import os


def checkup():
    try:
        import cha

        print(f"✓ Cha is installed")
    except:
        print("✗ Cha is NOT installed, skipping all tests!")
        pass

    # check if required environment variables are loaded
    try:
        from cha import config

        for platform in config.THIRD_PARTY_PLATFORMS:
            env_name = str(config.THIRD_PARTY_PLATFORMS[platform].get("env_name"))
            if env_name.lower().strip() == "ollama":
                continue
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
        print("✓ Tool ffmpeg seems to be installed")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("✗ Tool ffmpeg is not installed, please install it: https://ffmpeg.org/")

    # check if whisper model is installed and working
    try:
        from cha import config
        import whisper

        whisper_model_weight_file_path = (
            f"{str(Path.home())}/.cache/whisper/{config.DEFAULT_WHISPER_MODEL_NAME}.pt"
        )
        if os.path.isfile(whisper_model_weight_file_path) == False:
            whisper.load_model(config.DEFAULT_WHISPER_MODEL_NAME)
        print(f"✓ Whisper model found: {whisper_model_weight_file_path}")
    except Exception as e:
        print(f"✗ failed to find Whisper model {e}")

    # check to make sure at least one of the supported Terminal IDEs are installed
    try:
        from cha import config

        test_failed = True
        if any(shutil.which(editor) for editor in config.SUPPORTED_TERMINAL_IDES):
            print("✓ Supported Terminal IDE is installed")
            test_failed = False
        if test_failed:
            raise Exception(
                f"user's systems has none of the supported terminal text editor(s) installed"
            )
    except:
        print(f"✗ None of the supported terminal IDE(s) are installed")

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


if __name__ == "__main__":
    checkup()
