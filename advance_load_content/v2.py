import os
import sys


# Colors class for colored output.
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
    cmds = [
        "• cd <index>    : Enter a directory by its index.",
        "• cd <dir_name> : Enter a directory by its name.",
        "• cd ..       : Go up one directory.",
        "• Enter file number(s) (e.g. 1,2,3) : Toggle file selection (only applies to files).",
        "• list        : Show current directory listing and full selected files list (with removal option).",
        "• done        : Finish file selection (also triggered on CTRL-C/CTRL-D).",
    ]
    for cmd in cmds:
        print(colors.red(cmd))


def print_listing(current_dir, selected_files):
    entries = os.listdir(current_dir)
    dirs = sorted([e for e in entries if os.path.isdir(os.path.join(current_dir, e))])
    files = sorted([e for e in entries if os.path.isfile(os.path.join(current_dir, e))])
    print(colors.yellow("Current Directory:"), current_dir)
    print(colors.blue("Directories:"))
    for i, d in enumerate(dirs, start=1):
        print(f"  {i}) {colors.blue(d + '/')}")
    start_index = len(dirs) + 1
    print(colors.green("Files:"))
    for j, f in enumerate(files, start=start_index):
        full_path = os.path.join(current_dir, f)
        mark = "[x]" if full_path in selected_files else "[ ]"
        print(f"  {j}) {mark} {f}")
    if selected_files:
        print(colors.yellow("Selected files:"))
        sorted_sel = sorted(selected_files)
        for k, path in enumerate(sorted_sel, start=1):
            print(f"  {k}) {path}")


def traverse_and_select_files():
    current_dir = os.getcwd()
    selected_files = set()
    print_commands()
    print_listing(current_dir, selected_files)
    while True:
        try:
            user_input = input(colors.yellow("Enter command: ")).strip()
        except (KeyboardInterrupt, EOFError):
            print()  # Print a newline to separate output.
            break
        if user_input.lower() == "done":
            break
        tokens = user_input.split()
        # cd command handling.
        if tokens and tokens[0].lower() == "cd":
            if len(tokens) != 2:
                print(colors.red("Usage: cd <directory index|directory name> OR cd .."))
                continue
            arg = tokens[1]
            if arg == "..":
                parent = os.path.dirname(current_dir)
                if parent and parent != current_dir:
                    current_dir = parent
                    print_listing(current_dir, selected_files)
                else:
                    print(colors.red("Already at the top-most directory."))
                continue
            entries = os.listdir(current_dir)
            dirs = sorted(
                [e for e in entries if os.path.isdir(os.path.join(current_dir, e))]
            )
            # Check if arg is numeric (index) or a directory name.
            if arg.isdigit():
                idx = int(arg)
                if 1 <= idx <= len(dirs):
                    chosen = dirs[idx - 1]
                    current_dir = os.path.join(current_dir, chosen)
                    print_listing(current_dir, selected_files)
                else:
                    print(colors.red("Directory index out of range."))
            else:
                # Search for the directory by name.
                if arg in dirs:
                    current_dir = os.path.join(current_dir, arg)
                    print_listing(current_dir, selected_files)
                else:
                    print(
                        colors.red(f"Directory '{arg}' not found in current directory.")
                    )
            continue
        # list command handling: show current directory listing and allow removal from selected list.
        if tokens and tokens[0].lower() == "list":
            print_listing(current_dir, selected_files)
            if selected_files:
                removal = input(
                    colors.yellow(
                        "Enter number(s) (e.g. 1,2) to remove from selected files or press Enter to continue: "
                    )
                ).strip()
                if removal:
                    # Remove spaces and split by comma.
                    removal_indices = removal.replace(" ", "").split(",")
                    sorted_sel = sorted(selected_files)
                    for r in removal_indices:
                        if r.isdigit():
                            rem_idx = int(r)
                            if 1 <= rem_idx <= len(sorted_sel):
                                file_to_remove = sorted_sel[rem_idx - 1]
                                selected_files.remove(file_to_remove)
                                print(colors.yellow(f"Removed: {file_to_remove}"))
                            else:
                                print(colors.red(f"Invalid removal index: {rem_idx}"))
                        else:
                            print(colors.red(f"Invalid input for removal: {r}"))
            continue
        # Otherwise, assume file selection toggle.
        # Remove spaces and split by comma.
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
            file_idx = idx - start_index  # 0-indexed within files.
            filename = files[file_idx]
            full_path = os.path.join(current_dir, filename)
            if full_path in selected_files:
                selected_files.remove(full_path)
                print(colors.yellow(f"Unselected: {full_path}"))
            else:
                selected_files.add(full_path)
                print(colors.green(f"Selected: {full_path}"))
        # Do not reprint full listing on valid file toggles.
    return sorted(selected_files)


def msg_content_load_with_traversing(client):
    file_paths = traverse_and_select_files()
    if not file_paths:
        print(colors.red("No files were selected."))
        return None
    try:
        prompt = input(colors.yellow("Additional Prompt: "))
    except (KeyboardInterrupt, EOFError):
        print()  # Prevent overlapping prints.
        prompt = ""
    if prompt.strip() == "EDITOR":
        editor_content = check_terminal_editors_and_edit()
        if editor_content and editor_content.strip():
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
