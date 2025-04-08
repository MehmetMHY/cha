import os
import sys


# Placeholder for your colors; customize as needed.
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


def print_commands():
    cmds = (
        "COMMANDS: cd <index> to enter a directory, cd .. to go up, "
        "Enter a file number (or numbers with commas, e.g. 1,2,3) to toggle selection, "
        "list to reprint the current directory, done to finish."
    )
    print(colors.red(cmds))


def print_listing(current_dir, selected_files):
    # List directories and files in current_dir
    entries = os.listdir(current_dir)
    dirs = sorted([e for e in entries if os.path.isdir(os.path.join(current_dir, e))])
    files = sorted([e for e in entries if os.path.isfile(os.path.join(current_dir, e))])
    print(colors.yellow("Current Directory:"), current_dir)
    print(colors.blue("Directories:"))
    for i, d in enumerate(dirs, start=1):
        # Append a "/" at the end of each directory name.
        print(
            f"  {i}) {colors.blue(d + '/')}"
        )  # directories assumed selectable only via cd.
    start_index = len(dirs) + 1
    print(colors.green("Files:"))
    for j, f in enumerate(files, start=start_index):
        full_path = os.path.join(current_dir, f)
        mark = "[x]" if full_path in selected_files else "[ ]"
        print(f"  {j}) {mark} {f}")
    if selected_files:
        print(colors.yellow("Selected files:"))
        for path in sorted(selected_files):
            print("  -", path)


def traverse_and_select_files():
    current_dir = os.getcwd()
    selected_files = set()
    printed_commands = False
    # Print commands once at the very top in red.
    if not printed_commands:
        print_commands()
        printed_commands = True
    print_listing(current_dir, selected_files)
    while True:
        try:
            user_input = input(colors.yellow("Enter command: "))
        except (KeyboardInterrupt, EOFError):
            # Treat as 'done'
            break
        if not user_input.strip():
            continue
        tokens = user_input.strip().split()
        # if the user types "done", finish.
        if user_input.strip().lower() == "done":
            break
        # Handle cd commands.
        if tokens[0].lower() == "cd":
            # Check for 'cd ..'
            if len(tokens) == 2 and tokens[1] == "..":
                parent = os.path.dirname(current_dir)
                if parent and parent != current_dir:
                    current_dir = parent
                    print_listing(current_dir, selected_files)
                else:
                    print(colors.red("Already at the top-most directory."))
                continue
            # Check for 'cd' with a directory index.
            if len(tokens) == 2:
                try:
                    idx = int(tokens[1])
                except ValueError:
                    print(colors.red("Invalid directory index."))
                    continue
                entries = os.listdir(current_dir)
                dirs = sorted(
                    [e for e in entries if os.path.isdir(os.path.join(current_dir, e))]
                )
                if 1 <= idx <= len(dirs):
                    chosen = dirs[idx - 1]
                    current_dir = os.path.join(current_dir, chosen)
                    print_listing(current_dir, selected_files)
                else:
                    print(colors.red("Directory index out of range."))
                continue
            else:
                print(colors.red("Usage: cd <directory index> OR cd .."))
                continue
        # Handle explicit 'list' command.
        if tokens[0].lower() == "list":
            print_listing(current_dir, selected_files)
            continue
        # Otherwise, assume the input is a file selection.
        # Remove all spaces and split by commas.
        selection_str = user_input.replace(" ", "")
        indices = selection_str.split(",")
        valid = True
        chosen_indices = []
        for s in indices:
            if s.isdigit():
                chosen_indices.append(int(s))
            else:
                valid = False
                break
        if not valid:
            print(
                colors.red(
                    "Invalid input. Please enter file number(s) separated by commas, or a valid command."
                )
            )
            continue
        entries = os.listdir(current_dir)
        dirs = sorted(
            [e for e in entries if os.path.isdir(os.path.join(current_dir, e))]
        )
        files = sorted(
            [e for e in entries if os.path.isfile(os.path.join(current_dir, e))]
        )
        start_index = len(dirs) + 1
        max_index = start_index + len(files) - 1
        for idx in chosen_indices:
            if idx < start_index or idx > max_index:
                print(
                    colors.red(
                        f"Index {idx} is not a valid file selection in this directory."
                    )
                )
                continue
            file_idx = idx - start_index  # 0-indexed position in files list.
            filename = files[file_idx]
            full_path = os.path.join(current_dir, filename)
            if full_path in selected_files:
                selected_files.remove(full_path)
                print(colors.yellow(f"Unselected: {full_path}"))
            else:
                selected_files.add(full_path)
                print(colors.green(f"Selected: {full_path}"))
        # Don't reprint full listing on valid file toggles.
    return sorted(selected_files)


# Sample function integrating the selection with file loading.
def msg_content_load_with_traversing(client):
    file_paths = traverse_and_select_files()
    if not file_paths:
        print(colors.red("No files were selected."))
        return None
    prompt = input(colors.yellow("Additional Prompt: "))
    if prompt.strip() == "EDITOR":
        editor_content = check_terminal_editors_and_edit()
        if editor_content is not None and editor_content.strip():
            prompt = editor_content
            for line in prompt.rstrip("\n").split("\n"):
                print(colors.yellow(">"), line)
    contents = []
    try:
        for file_path in file_paths:
            print(colors.yellow(f"Loading {file_path}..."))
            content = load_most_files(
                client=client,
                file_path=file_path,
                model_name="your_default_model",
                prompt=prompt,
            )
            contents.append((file_path, content))
    except Exception as e:
        raise Exception(f"Failed to load files: {e}")
    output_lines = []
    if prompt:
        output_lines.append(f"PROMPT: {prompt}\n")
    for file_path, content in contents:
        output_lines.append(
            f"CONTENT FOR {file_path}:\n{'`'*10}\n{content}\n{'`'*10}\n"
        )
    output = "\n".join(output_lines)
    return output


# --- Stub helper implementations ---
def check_terminal_editors_and_edit():
    print(colors.yellow("Launching editor... (stub)"))
    return input("Enter prompt content here: ")


def load_most_files(client, file_path, model_name, prompt):
    with open(file_path, "r", encoding="utf8") as f:
        return f.read()


if __name__ == "__main__":
    client = None
    final_output = msg_content_load_with_traversing(client)
    if final_output:
        print(colors.yellow("Final combined output:"))
        print(final_output)
