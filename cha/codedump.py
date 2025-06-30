from datetime import datetime
import subprocess
import time
import os

from cha import colors, utils, config
import pathspec


def is_probably_binary_by_extension(file_path):
    _, ext = os.path.splitext(file_path.lower())
    return ext in config.BINARY_EXTENSIONS


def is_binary_file_by_sniff(file_path, num_bytes=1024):
    try:
        with open(file_path, "rb") as f:
            chunk = f.read(num_bytes)
            if b"\x00" in chunk:
                return True
    except:
        return True
    return False


def is_text_file(file_path):
    if is_probably_binary_by_extension(file_path):
        return False
    if is_binary_file_by_sniff(file_path):
        return False
    return True


def read_file(file_path):
    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    except:
        return None


def get_git_tracked_and_untracked_files(repo_path):
    try:
        cmd = ["git", "ls-files", "--exclude-standard", "--cached", "--others"]
        result = subprocess.run(
            cmd,
            cwd=repo_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
        )
        return result.stdout.splitlines()
    except:
        return []


def load_gitignore_patterns(dir_path):
    if not pathspec:
        return None
    gitignore_path = os.path.join(dir_path, ".gitignore")
    if not os.path.isfile(gitignore_path):
        return None
    try:
        with open(gitignore_path, "r", encoding="utf-8") as f:
            ignore_lines = f.read().splitlines()
        return pathspec.PathSpec.from_lines("gitwildmatch", ignore_lines)
    except:
        return None


def get_all_files_with_ignore(dir_path):
    spec = load_gitignore_patterns(dir_path)
    all_paths = []
    for root, dirs, files in os.walk(dir_path):
        for filename in files:
            full_path = os.path.join(root, filename)
            rel_path = os.path.relpath(full_path, dir_path)
            if spec and spec.match_file(rel_path):
                continue
            all_paths.append(rel_path)
    return all_paths


def interactive_exclusion(root_path, files_dict):
    excluded = set()

    all_dirs = set()
    for f in files_dict:
        d = os.path.dirname(f)
        while d and os.path.abspath(d) != os.path.abspath(root_path):
            all_dirs.add(d)
            parent = os.path.dirname(d)
            if parent == d:
                break
            d = parent

    directories = sorted(all_dirs)
    directories = [
        d for d in directories if os.path.abspath(d) != os.path.abspath(root_path)
    ]

    # Handle directory selection with fzf
    if directories:
        dir_display_list = [os.path.relpath(d, root_path) + "/" for d in directories]
        dir_map = {os.path.relpath(d, root_path) + "/": d for d in directories}
        fzf_input = "\n".join(dir_display_list)
        try:
            fzf_process = subprocess.run(
                [
                    "fzf",
                    "-m",
                    "--header",
                    "Use TAB to select multiple directories, ENTER to confirm.",
                ],
                input=fzf_input,
                capture_output=True,
                text=True,
                check=True,
                encoding="utf-8",
            )
            selected_display_dirs = fzf_process.stdout.strip().split("\n")
            if selected_display_dirs and selected_display_dirs[0]:
                selected_dirs = {
                    dir_map[d] for d in selected_display_dirs if d in dir_map
                }
                for f in list(files_dict.keys()):
                    if any(f.startswith(d) for d in selected_dirs):
                        excluded.add(f)
        except (subprocess.CalledProcessError, FileNotFoundError):
            return None

    # Handle file selection with fzf
    remaining_files = [f for f in files_dict.keys() if f not in excluded]
    if remaining_files:
        remaining_files_sorted = sorted(remaining_files)
        file_display_list = [
            os.path.relpath(rf, root_path) for rf in remaining_files_sorted
        ]
        path_map = {os.path.relpath(rf, root_path): rf for rf in remaining_files_sorted}
        fzf_input = "\n".join(file_display_list)
        try:
            fzf_process = subprocess.run(
                [
                    "fzf",
                    "-m",
                    "--header",
                    "Use TAB to select multiple files, ENTER to confirm.",
                ],
                input=fzf_input,
                capture_output=True,
                text=True,
                check=True,
                encoding="utf-8",
            )
            selected_display_files = fzf_process.stdout.strip().split("\n")
            if selected_display_files and selected_display_files[0]:
                for display_path in selected_display_files:
                    full_path = path_map.get(display_path)
                    if full_path:
                        excluded.add(full_path)
        except (subprocess.CalledProcessError, FileNotFoundError):
            return None

    return excluded


def get_tree_output(dir_path):
    try:
        cmd = ["tree", "--gitignore", "--prune", dir_path]
        result = subprocess.run(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True
        )
        return result.stdout
    except:
        return "Failed to generate tree output"


def generate_text_output(root_path, files_dict, excluded_files):
    included = [f for f in files_dict if f not in excluded_files]
    utc_now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    tree_output = get_tree_output(root_path)
    epoch_time = time.time()
    header = (
        "GENERAL INFORMATION/DATA:\n"
        "`````\n"
        f"CURRENT EPOCH TIME: {epoch_time} seconds\n"
        f"CURRENT UTC TIME: {utc_now}\n"
        f"ROOT DIR: {root_path}\n"
    )
    if included:
        header += "FILES:\n"
        for f in included:
            short_path = os.path.relpath(f, root_path)
            header += f"- {short_path}\n"
    header += "`````\n"
    header += "\nDIRECTORY STRUCTURE (TREE OUTPUT):\n`````\n"
    header += tree_output
    header += "`````\n"

    body = []
    for f in included:
        content = files_dict[f]
        short_path = os.path.relpath(f, root_path)
        section = (
            f"\nFILE PATH: {short_path}\n"
            "CONTENT:\n"
            "`````\n"
            f"{content}\n"
            "`````\n"
        )
        body.append(section)
    return header + "".join(body)


def extract_code(dir_path):
    root_path = os.path.abspath(dir_path)
    if os.path.isdir(os.path.join(root_path, ".git")):
        rel_paths = get_git_tracked_and_untracked_files(root_path)
    else:
        rel_paths = get_all_files_with_ignore(root_path)
    if not rel_paths:
        print(colors.red("No files found!"))
        return None
    files_dict = {}
    for rel in rel_paths:
        abs_path = os.path.join(root_path, rel)
        if is_text_file(abs_path):
            content = read_file(abs_path)
            if content is not None:
                files_dict[abs_path] = content
    if not files_dict:
        print(colors.red("No text files found!"))
        return None

    excluded_files = interactive_exclusion(root_path, files_dict)
    if excluded_files is None:
        return None

    output_text = generate_text_output(root_path, files_dict, excluded_files)
    token_count = utils.count_tokens(
        output_text, config.DEFAULT_SEARCH_BIG_MODEL, False
    )

    print(colors.yellow(f"{dir_path}"))
    print(colors.magenta(f"{token_count} Total Tokens"))

    return output_text


def code_dump(original_msg=None, save_file_to_current_dir=False, dir_full_path=None):
    try:
        dir_path = os.getcwd()
        if dir_full_path != None:
            if not os.path.isdir(dir_full_path):
                print(colors.red(f"'{dir_full_path}' is not a directory!"))
                return None
            dir_path = dir_full_path

        content = extract_code(dir_path)

        if content == None:
            return None

        if save_file_to_current_dir:
            file_name = f"code_dump_{int(time.time())}.txt"
            with open(file_name, "w") as file:
                file.write(content)
            print(colors.green(f"Saved codedump to: {file_name}"))
            return

        user_question = original_msg
        if user_question == None:
            user_question = input(colors.blue("Question: "))

        return utils.rls(
            f"""
            Here is original message:
            ```
            {user_question}
            ```

            And here is the entire code dump:

            =====[CODE DUMP STARTS]=====
            {content}
            ======[CODE DUMP ENDS]======

            Knowing this, can you answer the original message to the best of your ability given this context (codedump)?

            NOTE: Make sure not to mention the original message in your response just the answer to the user's question/message!
            """
        )
    except Exception as e:
        print(colors.red(f"Codedump failed due to: {e}"))
        return None
