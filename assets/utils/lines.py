from collections import defaultdict
from pathlib import Path
import fnmatch
import os


def parse_gitignore(gitignore_path):
    patterns = []
    if os.path.exists(gitignore_path):
        with open(gitignore_path, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    patterns.append(line)
    return patterns


def is_ignored(file_path, ignore_patterns, base_dir):
    rel_path = os.path.relpath(file_path, base_dir).replace("\\", "/")

    for pattern in ignore_patterns:
        if pattern.endswith("/"):
            pattern = pattern.rstrip("/")
            if any(part == pattern for part in rel_path.split("/")):
                return True
        else:
            if fnmatch.fnmatch(rel_path, pattern) or fnmatch.fnmatch(
                os.path.basename(file_path), pattern
            ):
                return True
            if "/" not in pattern and fnmatch.fnmatch(
                os.path.basename(file_path), pattern
            ):
                return True
    return False


def count_lines_in_file(file_path):
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return sum(1 for _ in f)
    except:
        return 0


def count_lines_by_extension(
    directory, ext_targets=None, show_largest_file=False, show_file_count=False
):
    if not os.path.exists(directory):
        print(f"Directory '{directory}' does not exist.")
        return

    gitignore_path = os.path.join(directory, ".gitignore")
    ignore_patterns = parse_gitignore(gitignore_path)

    extension_data = defaultdict(
        lambda: {"count": 0, "max_file": "", "max_lines": 0, "file_count": 0}
    )
    total_size = 0
    total_files = 0
    processed_dirs = set()

    for root, dirs, files in os.walk(directory):
        dirs[:] = [
            d
            for d in dirs
            if not is_ignored(os.path.join(root, d), ignore_patterns, directory)
        ]

        for file in files:
            file_path = os.path.join(root, file)

            if is_ignored(file_path, ignore_patterns, directory):
                continue

            if os.path.isfile(file_path):
                total_files += 1
                processed_dirs.add(root)
                total_size += os.path.getsize(file_path)
                ext = Path(file).suffix or "no_extension"
                if ext_targets and ext not in ext_targets:
                    continue
                line_count = count_lines_in_file(file_path)
                extension_data[ext]["count"] += line_count
                extension_data[ext]["file_count"] += 1
                if line_count > extension_data[ext]["max_lines"]:
                    extension_data[ext]["max_lines"] = line_count
                    extension_data[ext]["max_file"] = os.path.relpath(
                        file_path, directory
                    )

    print(f"Path: {dir_path}")
    total_num_dirs = len(processed_dirs)
    total_ext_types = len(extension_data)

    size_str = "0.00 KB"
    if total_size > 0:
        size_in_kb = total_size / 1024
        if size_in_kb > 1024:
            size_str = f"{size_in_kb / 1024:.2f} MB"
        else:
            size_str = f"{size_in_kb:.2f} KB"

    print(
        f"Files: {total_files} | Dirs: {total_num_dirs} | Exts: {total_ext_types} | Size: {size_str}"
    )

    if not extension_data:
        return

    fhd = "File Extension Stats:"
    if ext_targets == None:
        fhd = fhd.replace(":", " (ALL):")
    print(fhd)

    max_ext_len = max(
        len(".none" if "no_extension" in k else k) for k in extension_data.keys()
    )
    max_count_len = max(len(str(v["count"])) for v in extension_data.values())
    if show_largest_file:
        max_file_len = max(len(v["max_file"]) for v in extension_data.values())
        max_lines_len = max(len(str(v["max_lines"])) for v in extension_data.values())
    if show_file_count:
        max_file_count_len = max(
            len(str(v["file_count"])) for v in extension_data.values()
        )

    for ext, data in sorted(
        extension_data.items(), key=lambda item: item[1]["count"], reverse=True
    ):
        count = data["count"]
        if "no_extension" in ext:
            ext = ".none"

        output = f"{ext:<{max_ext_len}} = {str(count):>{max_count_len}} lines"
        if show_file_count:
            file_count = data["file_count"]
            output += f" | {str(file_count):>{max_file_count_len}} files"
        if show_largest_file:
            max_file = data["max_file"]
            max_lines = data["max_lines"]
            output += f" | {max_file:<{max_file_len}} = {str(max_lines):>{max_lines_len}} lines"
        print(output)


if __name__ == "__main__":
    dir_path = os.path.dirname(os.path.abspath(__file__))
    dir_path = "/".join(dir_path.split("/")[:-2]) + "/"
    ext_targets = [".py", ".sh", ".md"]
    count_lines_by_extension(
        directory=dir_path,
        ext_targets=ext_targets,
        show_largest_file=True,
        show_file_count=True,
    )
