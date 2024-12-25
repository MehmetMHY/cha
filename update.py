# NOTE: the goal of this script is to easily update the dependencies in Cha's "setup.py" file

import subprocess
import re

if __name__ == "__main__":
    # read the current setup.py
    with open("setup.py", "r") as f:
        content = f.read()

    # get and update version
    version_match = re.search(r'version="([^"]*)"', content)
    if version_match:
        current_version = version_match.group(1)
        print(f"Current version: {current_version}")
        new_version = input("Enter new version: ").strip()
        content = content.replace(
            f'version="{current_version}"', f'version="{new_version}"'
        )

    # find all dependencies
    deps = re.findall(r'"([^"]+)==([^"]+)"', content)

    # update each dependency
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
                    print(f"Updating {package}: {current_version} -> {latest_version}")
                    content = content.replace(
                        f'"{package}=={current_version}"',
                        f'"{package}=={latest_version}"',
                    )
                    break

        except subprocess.CalledProcessError:
            print(f"Failed to get version for {package}, skipping...")
            continue

    # write updated content
    with open("setup.py", "w") as f:
        f.write(content)
    print(f"Updated setup.py file!")

    print(f"Run ONE of the following commands to update Cha locally:")
    print(f"- pip3 install -e .")
    print(f"- pip3 install .")
