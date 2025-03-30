import openai
import json
import uuid
import os
import re

# NOTE: last updated on March 29, 2025
FILETYPE_TO_EXTENSION = {
    # Programming Languages
    "python": ".py",
    "py": ".py",
    "bash": ".sh",
    "sh": ".sh",
    "shell": ".sh",
    "zsh": ".zsh",
    "fish": ".fish",
    "powershell": ".ps1",
    "ps1": ".ps1",
    "bat": ".bat",
    "cmd": ".cmd",
    "javascript": ".js",
    "js": ".js",
    "typescript": ".ts",
    "ts": ".ts",
    "coffee": ".coffee",
    "vue": ".vue",
    "jsx": ".jsx",
    "tsx": ".tsx",
    "java": ".java",
    "c": ".c",
    "h": ".h",
    "hpp": ".hpp",
    "c++": ".cpp",
    "cpp": ".cpp",
    "cxx": ".cpp",
    "cc": ".cpp",
    "cs": ".cs",  # C#
    "go": ".go",
    "golang": ".go",
    "php": ".php",
    "rb": ".rb",  # Ruby
    "ruby": ".rb",
    "swift": ".swift",
    "kotlin": ".kt",
    "kt": ".kt",
    "rs": ".rs",  # Rust
    "rust": ".rs",
    "dart": ".dart",
    "r": ".r",
    "m": ".m",  # MATLAB/Objective-C
    "matlab": ".m",
    "mm": ".mm",  # Objective-C++
    "scala": ".scala",
    "lua": ".lua",
    "perl": ".pl",
    "pl": ".pl",
    "pm": ".pm",
    "tcl": ".tcl",
    "groovy": ".groovy",
    "gradle": ".gradle",
    "clojure": ".clj",
    "clj": ".clj",
    "cljs": ".cljs",
    "cljc": ".cljc",
    "fsharp": ".fs",
    "fs": ".fs",
    "elixir": ".ex",
    "ex": ".ex",
    "exs": ".exs",
    "asp": ".asp",
    "aspx": ".aspx",
    "jsp": ".jsp",
    "sas": ".sas",
    "d": ".d",  # D language
    "pas": ".pas",  # Pascal
    "pp": ".pp",  # Free Pascal
    "asm": ".asm",  # Assembly
    "s": ".s",
    "v": ".v",  # Verilog
    "sv": ".sv",  # SystemVerilog
    "vhd": ".vhd",
    "vhdl": ".vhdl",
    "cl": ".cl",  # OpenCL
    # Markup, Data, and Config
    "html": ".html",
    "htm": ".htm",
    "css": ".css",
    "sass": ".sass",
    "scss": ".scss",
    "xml": ".xml",
    "svg": ".svg",
    "svgz": ".svgz",
    "yaml": ".yaml",
    "yml": ".yml",
    "toml": ".toml",
    "ini": ".ini",
    "cfg": ".cfg",
    "conf": ".conf",
    "json": ".json",
    "json5": ".json5",
    "jsonc": ".jsonc",
    "sql": ".sql",
    "tsql": ".sql",
    "pgsql": ".sql",
    "db2": ".sql",
    "csv": ".csv",
    "tsv": ".tsv",
    "proto": ".proto",
    "proto3": ".proto",
    "ipynb": ".ipynb",
    "md": ".md",
    "markdown": ".md",
    "rst": ".rst",
    "org": ".org",
    "latex": ".tex",
    "tex": ".tex",
    "rmd": ".Rmd",
    "rmarkdown": ".Rmd",
    "rproj": ".Rproj",
    "properties": ".properties",
    "inf": ".inf",
    "plist": ".plist",
    # Plain Text & Documentation
    "txt": ".txt",
    "text": ".txt",
    "plaintext": ".txt",
    "rtf": ".rtf",
    "doc": ".doc",
    "docx": ".docx",
    "odt": ".odt",
    "ppt": ".ppt",
    "pptx": ".pptx",
    "pdf": ".pdf",
    "xls": ".xls",
    "xlsx": ".xlsx",
    "ods": ".ods",
    "rtfd": ".rtfd",
    "man": ".man",
    # Shell / Build / System / Others
    "makefile": ".makefile",
    "dockerfile": ".dockerfile",
    "docker-compose": ".yml",
    "gitignore": ".gitignore",
    "gitattributes": ".gitattributes",
    "editorconfig": ".editorconfig",
    "eslint": ".eslintrc.js",
    "eslintjson": ".eslintrc.json",
    "npmrc": ".npmrc",
    "babelrc": ".babelrc",
    "prettierrc": ".prettierrc",
    "gradlew": ".gradlew",
    "env": ".env",
    "nvmrc": ".nvmrc",
    "npmignore": ".npmignore",
    "dockerignore": ".dockerignore",
    "clang-format": ".clang-format",
    "clang-tidy": ".clang-tidy",
    "desktop": ".desktop",
    "service": ".service",
    "socket": ".socket",
    "timer": ".timer",
    "target": ".target",
    # Misc File Types
    "jpg": ".jpg",
    "jpeg": ".jpeg",
    "png": ".png",
    "gif": ".gif",
    "bmp": ".bmp",
    "webp": ".webp",
    "ico": ".ico",
    "tiff": ".tiff",
    "tga": ".tga",
    "psd": ".psd",
    "xcf": ".xcf",
    "exr": ".exr",
    "hdr": ".hdr",
    "mp4": ".mp4",
    "mkv": ".mkv",
    "mov": ".mov",
    "avi": ".avi",
    "mpg": ".mpg",
    "mpeg": ".mpeg",
    "flv": ".flv",
    "f4v": ".f4v",
    "swf": ".swf",
    "mp3": ".mp3",
    "wav": ".wav",
    "flac": ".flac",
    "ogg": ".ogg",
    "wma": ".wma",
    "ape": ".ape",
    "aiff": ".aiff",
    "au": ".au",
    "caf": ".caf",
    "mid": ".mid",
    "midi": ".midi",
    "xm": ".xm",
    "it": ".it",
    "s3m": ".s3m",
    "mod": ".mod",
    "zip": ".zip",
    "7z": ".7z",
    "gz": ".gz",
    "xz": ".xz",
    "lz": ".lz",
    "lzma": ".lzma",
    "lzo": ".lzo",
    "lzop": ".lzop",
    "cpio": ".cpio",
    "z": ".z",
    "tar": ".tar",
    "tgz": ".tgz",
    "bz2": ".bz2",
    "rar": ".rar",
    "ps": ".ps",
    "eps": ".eps",
    "ai": ".ai",
}


def extract_code_blocks(text):
    output = {"created": [], "errors": [], "total": 0}

    pattern = r"```([a-zA-Z0-9+\-#]*)\n(.*?)```"
    matches = re.findall(pattern, text, re.DOTALL)
    for lang, code in matches:
        output["total"] += 1
        filename = None
        try:
            lang = lang.strip().lower() if lang else None
            extension = FILETYPE_TO_EXTENSION.get(lang, ".txt")

            filename = (
                "cha_extract_" + str(uuid.uuid4()).replace("-", "")[:8] + extension
            )
            filename = os.path.join(os.getcwd(), filename)
            with open(filename, "w", encoding="utf-8") as f:
                f.write(code.strip())

            output["created"].append(filename)
        except Exception as e:
            output["errors"].append(e)
            if filename != None and os.path.exists(filename):
                os.remove(filename)

    return output


if __name__ == "__main__":
    client = openai.OpenAI()

    system_prompt = (
        "You are a helpful assistant. Always return any code or file output in a Markdown code fence "
        "with the syntax ```<language or filetype>\n...``` so it can be parsed automatically."
    )

    user_input = input("PROMPT: ")

    chat_history = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_input},
    ]

    response = client.chat.completions.create(
        model="gpt-4o", messages=chat_history, stream=True
    )

    content = ""
    for chunk in response:
        if chunk.choices[0].delta.content is not None:
            txt = chunk.choices[0].delta.content
            print(txt, end="", flush=True)
            content += txt
    print()

    print("\n========[OUTPUT]========\n")

    output = extract_code_blocks(content)

    print(json.dumps(output, indent=4))
