# NOTE: the goal of this script is to easily update the dependencies in Cha's SETUP file
# NOTE: make sure to run this script in the root directory of the Cha project

import subprocess
import sys
import os
import re


def save_input(starting_text):
    try:
        return input(starting_text)
    except (KeyboardInterrupt, EOFError):
        print()
        sys.exit(1)


if __name__ == "__main__":
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
    confirm_input = save_input(f"Continue with this path (Y/n)? ")
    if confirm_input.lower() in ["n", "no"]:
        PYTHON_SETUP_FILE_PATH = save_input(
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
        new_version = save_input("Enter new version: ").strip()
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
    user_input = save_input(f"Do you like to reinstall Cha (Y/n)? ")
    if user_input.lower() in ["y", "yes"]:
        user_input = save_input('Install without "-e" option (Y/n)? ')
        if user_input.lower() in ["y", "yes"]:
            print('> Installing Cha WITHOUT "-e" Option!')
            os.system("pip3 install .")
        else:
            print('> Installing Cha WITH "-e" Option!')
            os.system("pip3 install -e .")
