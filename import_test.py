import uuid
import os


def find_python_files(base_dir):
    py_files = []
    for root, _, files in os.walk(base_dir):
        for file in files:
            if file.endswith(".py"):
                py_files.append(os.path.join(root, file))
    return py_files


def load_file(filename):
    with open(filename, "r", encoding="utf-8") as file:
        return [line.rstrip("\n") for line in file]


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    py_files = find_python_files(base_dir)
    generated_script_paths = []  # To store paths of generated test scripts

    for path in py_files:
        if os.path.abspath(path) == os.path.abspath(
            __file__
        ):  # Avoid processing the script itself
            continue

        lines = load_file(path)

        new_file_uuid = uuid.uuid4()
        new_filename = f"test_{new_file_uuid}.py"
        new_filepath = os.path.join(base_dir, new_filename)

        with open(new_filepath, "w", encoding="utf-8") as new_file:
            new_file.write(f"# {new_file_uuid}\n")
            new_file.write(f"# original file path: {path}\n")
            new_file.write("\n")
            new_file.write("import time\n")
            new_file.write("import os\n")  # Added import os for os.path.basename
            new_file.write("start_time = time.time()\n")
            new_file.write("\n")  # Add a newline for better separation

            for line in lines:
                if line.startswith("import") or line.startswith("from"):
                    new_file.write(f"{line}\n")

            new_file.write("\n")  # Add a newline for better separation
            new_file.write("runtime = time.time() - start_time\n")
            # Modified print statement to use os.path.basename
            new_file.write(
                'print(f"File: {os.path.basename(__file__)}, Runtime: {runtime} seconds")\n'
            )

        generated_script_paths.append(new_filepath)  # Store path for run script
        print(f"Created: {new_filepath}")

    # Create the test_run.sh script
    run_script_filename = "test_run.sh"
    run_script_filepath = os.path.join(base_dir, run_script_filename)
    with open(run_script_filepath, "w", encoding="utf-8") as run_file:
        run_file.write("#!/bin/bash\n")
        run_file.write('echo "Running all generated test scripts..."\n')
        for script_path in generated_script_paths:
            # Use os.path.abspath to ensure the path is absolute for the script
            run_file.write(f'python3 "{os.path.abspath(script_path)}"\n')

    # Make the script executable
    os.chmod(run_script_filepath, 0o755)
    print(f"Created run script: {run_script_filepath}")


if __name__ == "__main__":
    main()
