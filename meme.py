import subprocess

all_imports = [
    "PIL.Image",
    "anthropic",
    "bs4",
    "contextlib",
    "datetime",
    "datetime",
    "docx.Document",
    "duckduckgo_search.DDGS",
    "moviepy.VideoFileClip",
    "mutagen.File",
    "pydantic.BaseModel",
    "requests.adapters.HTTPAdapter",
    "requests.packages.urllib3.util.retry.Retry",
    "youtube_transcript_api.YouTubeTranscriptApi",
    "argparse",
    "base64",
    "chardet",
    "concurrent.futures",
    "copy",
    "datetime",
    "fitz",
    "importlib",
    "importlib.util",
    "itertools",
    "json",
    "math",
    "openpyxl",
    "os",
    "pathspec",
    "pytesseract",
    "random",
    "re",
    "requests",
    "statistics",
    "string",
    "subprocess",
    "sys",
    "tempfile",
    "threading",
    "tiktoken",
    "time",
    "uuid",
    "warnings",
]

packages_to_test = [
    "openai",
    "anthropic",
    "bs4",
    "yt_dlp",
    "youtube_transcript_api",
    "fitz",
    "tiktoken",
    "duckduckgo_search",
    "docx",
    "openpyxl",
    "chardet",
    "pathspec",
    "faster_whisper",
    "moviepy",
    "PIL",
    "pytesseract",
    "mutagen",
]

packages_to_test = list(set(packages_to_test + all_imports))


def measure_import_times(modules):
    """
    For each module in 'modules', run:
      python -X importtime -c "import <module>"
    Parse the final cumulative time in microseconds from the stderr output.
    Return a dict of {module_name: cumulative_time_us}.
    """
    results = {}
    for mod in modules:
        cmd = ["python", "-X", "importtime", "-c", f"import {mod}"]
        proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        out, err = proc.communicate()

        # Lines come back in stderr in the format:
        #   import time: self [us] | cumulative [us] | <something>
        # We'll look for the final line to get the total cumulative import time
        lines = [
            line.strip() for line in err.splitlines() if line.startswith("import time:")
        ]
        if not lines:
            # no lines => either no timing info or import failed
            results[mod] = 0
            continue

        last_line = lines[-1]
        # example: "import time: 123 | 9999 | some\path\to.py"
        parts = last_line.replace("import time:", "").strip().split("|")
        if len(parts) < 2:
            results[mod] = 0
            continue

        try:
            cumulative_us = int(parts[1].strip())
        except ValueError:
            cumulative_us = 0
        results[mod] = cumulative_us

    return results


if __name__ == "__main__":
    print("Measuring import times for:")
    for pkg in packages_to_test:
        print("  ", pkg)

    import_times = measure_import_times(packages_to_test)

    # Sort descending by import time
    sorted_times = sorted(import_times.items(), key=lambda x: x[1], reverse=True)

    # Print final results
    print("\n\nImport times (microseconds), descending:\n")
    for pkg, microsec in sorted_times:
        print(f"{pkg:<25s} {microsec:>10} µs")
