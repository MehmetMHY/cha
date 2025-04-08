import os


# Placeholder for your colors, replace with your own implementation
class Colors:
    def red(self, s):
        return f"\033[91m{s}\033[0m"

    def yellow(self, s):
        return f"\033[93m{s}\033[0m"

    def blue(self, s):
        return f"\033[94m{s}\033[0m"

    def green(self, s):
        return f"\033[92m{s}\033[0m"


colors = Colors()


def traverse_and_select_files():
    """
    A simple CLI file browser for navigating directories and selecting files.

    Commands:
      - cd <index>    : Enter a directory (as displayed in the listing)
      - up            : Go up one directory (if not at root)
      - select <indices> or toggle <indices> : Toggle selection for file(s)
            Type numbers separated by commas (e.g.: 1,3,4)
      - list          : Redisplay the current directory listing
      - done          : Finish selecting files
    """
    current_dir = os.getcwd()
    selected_files = set()  # a set of full file paths

    while True:
        print("\n" + colors.yellow("Current Directory:"), current_dir)

        # List contents: get directories and files; show directories first.
        entries = os.listdir(current_dir)
        dirs = sorted(
            [e for e in entries if os.path.isdir(os.path.join(current_dir, e))]
        )
        files = sorted(
            [e for e in entries if os.path.isfile(os.path.join(current_dir, e))]
        )

        # We'll display two separate indices (but using one numbering scheme)
        print(colors.blue("\nDirectories:"))
        for i, d in enumerate(dirs, start=1):
            print(f"   {i}) {colors.blue(d)}")
        dir_count = len(dirs)

        print(colors.green("\nFiles:"))
        for j, f in enumerate(files, start=dir_count + 1):
            full_path = os.path.join(current_dir, f)
            sel_mark = "[x]" if full_path in selected_files else "[ ]"
            print(f"   {j}) {sel_mark} {f}")

        # Show summary of currently selected files (full paths)
        if selected_files:
            print("\n" + colors.yellow("Current file selection:"))
            for path in sorted(selected_files):
                print("  -", path)
        else:
            print("\n" + colors.yellow("No files selected currently."))

        # Get a command from the user
        print(
            "\nCommands: cd <index>, up, select <indices>, toggle <indices>, list, done"
        )
        command = input(colors.yellow("Enter command: ")).strip()
        if not command:
            continue

        if command.lower() == "done":
            break

        parts = command.split()
        cmd = parts[0].lower()

        # Command: move up a directory
        if cmd == "up":
            parent = os.path.dirname(current_dir)
            # Only change directory if going up makes sense
            if parent and parent != current_dir:
                current_dir = parent
            else:
                print(colors.red("Already at the top-most directory."))
            continue

        # Command: change directory: cd <index>
        if cmd == "cd":
            if len(parts) != 2:
                print(colors.red("Usage: cd <directory index>"))
                continue
            try:
                idx = int(parts[1])
                # Ensure the index falls in the directories list
                if 1 <= idx <= len(dirs):
                    chosen = dirs[idx - 1]
                    current_dir = os.path.join(current_dir, chosen)
                else:
                    print(colors.red("Invalid directory index"))
            except ValueError:
                print(colors.red("Invalid index entered."))
            continue

        # Commands to (toggle) select files: 'select' or 'toggle'
        if cmd in ("select", "toggle"):
            if len(parts) != 2:
                print(colors.red("Usage: select <file indices separated by commas>"))
                continue
            indices_str = parts[1].split(",")
            for s in indices_str:
                try:
                    idx = int(s)
                except ValueError:
                    print(colors.red(f"Invalid number: {s}"))
                    continue
                # Check if this index falls into files portion
                file_idx = (
                    idx - dir_count
                )  # index within the files list (starting at 1)
                if file_idx < 1 or file_idx > len(files):
                    print(colors.red(f"Index {idx} is not a file index."))
                else:
                    filename = files[file_idx - 1]
                    full_path = os.path.join(current_dir, filename)
                    if full_path in selected_files:
                        selected_files.remove(full_path)
                        print(colors.yellow(f"Unselected: {full_path}"))
                    else:
                        selected_files.add(full_path)
                        print(colors.green(f"Selected: {full_path}"))
            continue

        # Command: list to re-display (could always loop, but included just in case)
        if cmd == "list":
            continue

        print(colors.red("Unknown command."))
    return sorted(selected_files)


# Sample function integrating the selection with file loading:
def msg_content_load_with_traversing(client):
    # Let the user browse and select files (with full paths)
    file_paths = traverse_and_select_files()
    if not file_paths:
        print(colors.red("No files were selected."))
        return None

    # Allow an additional prompt as before
    prompt = input(colors.yellow("Additional Prompt: "))

    # Optional: Launch a text editor if special input mode is chosen
    if (
        prompt.strip() == "EDITOR"
    ):  # for example, you could compare with config.TEXT_EDITOR_INPUT_MODE
        # Assume check_terminal_editors_and_edit() is defined
        editor_content = check_terminal_editors_and_edit()
        if editor_content is not None and editor_content.strip():
            prompt = editor_content
            for line in prompt.rstrip("\n").split("\n"):
                print(colors.yellow(">"), line)

    contents = []
    try:
        for file_path in file_paths:
            print(colors.yellow(f"Loading {file_path}..."))
            # Note: load_most_files should load the content of the given file.
            content = load_most_files(
                client=client,
                file_path=file_path,
                model_name="your_default_model",  # replace with your configuration option
                prompt=prompt,
            )
            contents.append((file_path, content))
    except Exception as e:
        raise Exception(f"Failed to load files: {e}")

    # Build a summary output of the loaded content
    output_lines = []
    if prompt:
        output_lines.append(f"PROMPT: {prompt}\n")
    for file_path, content in contents:
        output_lines.append(
            f"CONTENT FOR {file_path}:\n{'`'*10}\n{content}\n{'`'*10}\n"
        )
    output = "\n".join(output_lines)
    return output


# --- Helpers (stub implementations) ---


def check_terminal_editors_and_edit():
    # Stub: open user's editor and return the content they typed.
    print(colors.yellow("Launching editor... (stub)"))
    return input("Enter prompt content here: ")


def load_most_files(client, file_path, model_name, prompt):
    # Stub: load the file content and process it; replace with your implementation.
    with open(file_path, "r", encoding="utf8") as f:
        return f.read()


# Example usage:
if __name__ == "__main__":
    # Stub client; replace with your actual client object.
    client = None
    final_output = msg_content_load_with_traversing(client)
    if final_output:
        print("\nFinal combined output:")
        print(final_output)
