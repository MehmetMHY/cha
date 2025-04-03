"""
April 2, 2025

The goal of this script is to time the import time for all packages in Cha

This code is far from perfect but was good enough to improve Cha's initial interactive mode startup time from ~2.3 seconds to ~1.23 seconds on my personal laptop (2019 16-inch MacBook Pro with an Intel i9)

If you can make this script better, please make a PR! :)
"""

import subprocess
import time
import json
import sys
import os


def underline(text):
    return "\033[4m" + text + "\033[0m"


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


def all_py_imports_in_dir(dir_path):
    python_files = [f for f in os.listdir(dir_path) if f.endswith(".py")]

    output = []
    for py_file in python_files:
        file_path = os.path.join(dir_path, py_file)
        with open(file_path, "r") as file:
            content = file.read()
        content = content.split("\n")
        for line in content:
            line = line.strip()
            if "setup.py" in file_path and "==" in line:
                line = line.split("==")[0].replace('"', "").replace("'", "").strip()
                output.append(line)
            elif line.startswith("import"):
                line = line.split("#")[0].strip()
                line = line.replace("import ", "").strip().replace(" ", "").split(",")
                for l in line:
                    output.append(l)
            elif line.startswith("from"):
                line = line.split("#")[0].strip().split(" ")[1]
                output.append(line)

    return output


if __name__ == "__main__":
    # grab ALL imports in Cha

    start_time = time.time()

    dir_path = os.path.dirname(os.path.abspath(__file__))

    cha_root_dir = "/".join(dir_path.split("/")[:-1])

    dir_targets = [cha_root_dir, f"{cha_root_dir}/cha/"]

    packages_to_test = []
    for d in dir_targets:
        imports = all_py_imports_in_dir(d)
        for i in imports:
            if i not in packages_to_test:
                if "cha" not in i:
                    packages_to_test.append(i)

    packages_to_test = list(set(packages_to_test))

    # measure import time for all founded imports

    print(underline("Measuring import times for:"))
    for pkg in packages_to_test:
        print("  ", pkg)

    import_times = measure_import_times(packages_to_test)

    sorted_times = sorted(import_times.items(), key=lambda x: x[1], reverse=True)

    print(underline("Import times (microseconds), descending:"))
    for pkg, microsec in sorted_times:
        print(f"{microsec:>10} µs -> {pkg}")

    runtime = time.time() - start_time

    print(underline("Total Runtime:"))
    print(f"{runtime} seconds")
