from lingua import LanguageDetectorBuilder
import subprocess
import platform
import time
import json

from cha import colors, config


def run_command(command):
    try:
        result = subprocess.run(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return result.stdout
    except:
        return None


def get_current_os():
    os_name = platform.system()
    if os_name == "Darwin":
        return "macos"
    elif os_name == "Linux":
        return "linux"
    elif os_name == "Windows":
        return "windows"
    else:
        return None


def detect_languages_optimized(detector, text):
    detected_language = detector.detect_language_of(text)
    if detected_language:
        return [
            {"language": detected_language, "start_index": 0, "end_index": len(text)}
        ]

    segments = list(detector.detect_multiple_languages_of(text))
    if not segments:
        return [{"language": None, "start_index": 0, "end_index": len(text)}]

    merged_segments = []
    current_segment = {
        "language": segments[0].language,
        "start_index": segments[0].start_index,
        "end_index": segments[0].end_index,
    }

    for i in range(1, len(segments)):
        segment = segments[i]
        if segment.language == current_segment["language"]:
            current_segment["end_index"] = segment.end_index
        else:
            merged_segments.append(current_segment)
            current_segment = {
                "language": segment.language,
                "start_index": segment.start_index,
                "end_index": segment.end_index,
            }

    merged_segments.append(current_segment)
    return merged_segments


def process_espeak_voice(detector, text):
    segments = detect_languages_optimized(detector, text)

    for segment in segments:
        segment_text = text[segment["start_index"] : segment["end_index"]]
        lang = segment["language"]

        if lang and lang.name in config.NORMALIZED_LANGUAGE_MAPPING:
            espeak_code = config.NORMALIZED_LANGUAGE_MAPPING[lang.name]["espeak_code"]
            run_command(
                f'espeak-ng -v "{espeak_code}" -s 145 -p 55 -a 180 "{segment_text}"'
            )
        else:
            run_command(f'espeak-ng -s 145 -p 55 -a 180 "{segment_text}"')


def process_say_voice(detector, text):
    segments = detect_languages_optimized(detector, text)

    for segment in segments:
        segment_text = text[segment["start_index"] : segment["end_index"]]
        lang = segment["language"]

        if lang and lang.name in config.NORMALIZED_LANGUAGE_MAPPING:
            say_voice = config.NORMALIZED_LANGUAGE_MAPPING[lang.name]["say_voice_name"]
            if say_voice:
                run_command(f'say -v "{say_voice}" "{segment_text}"')
            else:
                run_command(f'say "{segment_text}"')
        else:
            run_command(f'say "{segment_text}"')


def voice_tool(text):
    if not text.strip():
        return

    detector = (
        LanguageDetectorBuilder.from_all_languages()
        .with_preloaded_language_models()
        .build()
    )

    current_os = get_current_os()

    if not current_os:
        print(colors.red("Unsupported operating system"))
        return

    try:
        if current_os == "macos":
            process_say_voice(detector, text)
        else:
            espeak_installed = run_command("espeak-ng --version")
            if not espeak_installed or len(espeak_installed.strip()) == 0:
                print(
                    colors.red(
                        "The espeak-ng text-to-speech engine package is not installed. See installation guide at: https://github.com/espeak-ng/espeak-ng/"
                    )
                )
                return
            else:
                process_espeak_voice(detector, text)
    except Exception:
        print(colors.red("Speech processing failed"))
