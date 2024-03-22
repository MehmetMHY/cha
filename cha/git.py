import subprocess
import shutil
import json
import uuid
import sys
import os


def read_file(path):
    try:
        with open(str(path), "r", encoding="utf-8") as file:
            content = [line for line in file]
        return content
    except:
        return None


def write_file(file_name, text):
    with open(file_name, "w") as file:
        file.write(text)


def read_json(path):
    with open(str(path)) as file:
        content = json.load(file)
    return content


def write_json(path, data):
    with open(str(path), "w") as file:
        json.dump(data, file, indent=4)


def execute(cmd):
    proc = subprocess.Popen(
        str(cmd),
        shell=True,
        stdout=subprocess.PIPE,
    )
    output = proc.communicate()[0].decode("utf-8")
    return output.split("\n")


def get_repo_files(directory):
    file_paths = []
    for root, dirs, files in os.walk(directory):
        for filename in files:
            filepath = os.path.join(root, filename)
            if "/.git/" in filepath:
                continue
            if "/.github/" in filepath:
                continue
            if filepath.split("/")[-1] == ".gitignore":
                continue
            if filepath.split("/")[-1] == ".gitmodules":
                continue
            file_paths.append(filepath)
    return file_paths


def raw_git_scrape(repo_url):
    # extract and create names
    repo_id = str(uuid.uuid4())
    repo_name = repo_url.split("/")[-1].replace(".git", "").replace(".", "-")
    filename = os.path.join(os.getcwd(), f"cha_{repo_name}_{repo_id}")
    git_command = f"git clone --depth 1 {repo_url} {filename}"

    # run git command
    execute(git_command)

    # build prompt using code in the git project
    files = get_repo_files(filename)
    prompt = f"Here is all the code for the '{repo_name}' project:\n\n"
    for file in files:
        content = read_file(file)
        if content == None:
            continue
        prompt += f"{file.replace(filename, repo_name)}\n```\n"
        prompt += "".join(content)
        prompt += "\n```\n\n"

    # delete cloned git project
    shutil.rmtree(filename)

    return {"prompt": prompt, "command": git_command, "filepath": filename}


def valid_git_url(url):
    if "github.com" not in str(url):
        return False
    if str(url).endswith(".git") == False:
        return False
    return True


def git_scrape(repo_url):
    try:
        output = raw_git_scrape(repo_url)
        return output["prompt"]
    except:
        return None
