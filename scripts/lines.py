import json
import os


def load_file(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        content = file.read()
    return content


def get_all_file_paths(directory_path):
    if not os.path.isdir(directory_path):
        raise ValueError(f"dir '{directory_path}' does not exist!")

    file_paths = []
    for root, _, files in os.walk(directory_path):
        for file_name in files:
            file_paths.append(os.path.join(root, file_name))

    return file_paths


if __name__ == "__main__":
    dir_path = "/".join(os.getcwd().split("/")[:-1]) + "/"

    all_file_paths = get_all_file_paths(dir_path)

    ign_dir_sub_names = [
        "egg-info/",
        ".git/",
        "build/",
        "__pycache__/",
        ".DS_Store",
        "env/",
        ".env",
        # project specific dirs
        "cha/docker/",
        "cha/scripts/",
    ]

    file_paths = []
    for file in all_file_paths:
        skip_it = False
        for i in ign_dir_sub_names:
            if i in file:
                skip_it = True
                break
        if skip_it:
            continue
        if file.endswith(".py") == False:
            continue
        file_paths.append(file)

    all_lines = []
    for file_path in file_paths:
        lines = load_file(file_path).split("\n")
        if len(lines) == 0:
            continue
        for line in lines:
            tmp = line.strip()
            if len(tmp) == 0:
                continue
            if tmp.startswith("#"):
                continue
            all_lines.append(line)

    line_count = int(len(all_lines) * 1.05)

    print(line_count)
