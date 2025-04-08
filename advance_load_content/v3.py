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
    print(colors.red("Commands List:"))
    cmds = [
        "- cd <index>         : Enter a directory by its index.",
        "- cd <dir_name>      : Enter a directory by its name.",
        "- cd ..              : Go up one directory.",
        "- ls                 : Show current directory and selected files.",
        "- list               : Show current directory and selected files with removal option.",
        "- Enter file number(s) (e.g. 1,2,3): Toggle file selection (only for files).",
        "- done               : Finish selection (also triggered on CTRL-C/CTRL-D).",
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
            print()  # Separate output from any following prompt.
            break
        if user_input.lower() == "done":
            break
        tokens = user_input.split()
        # Handle cd command.
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
            # If argument is digit, treat as index.
            if arg.isdigit():
                idx = int(arg)
                if 1 <= idx <= len(dirs):
                    chosen = dirs[idx - 1]
                    current_dir = os.path.join(current_dir, chosen)
                    print_listing(current_dir, selected_files)
                else:
                    print(colors.red("Directory index out of range."))
            else:
                # Otherwise, treat as directory name.
                if arg in dirs:
                    current_dir = os.path.join(current_dir, arg)
                    print_listing(current_dir, selected_files)
                else:
                    print(
                        colors.red(f"Directory '{arg}' not found in current directory.")
                    )
            continue

        # ls command: simply list state.
        if tokens and tokens[0].lower() == "ls":
            print_listing(current_dir, selected_files)
            continue

        # list command: list and prompt for removal of selected files.
        if tokens and tokens[0].lower() == "list":
            print_listing(current_dir, selected_files)
            if selected_files:
                removal = input(
                    colors.yellow(
                        "Enter number(s) (e.g. 1,2) to remove from selected files or press Enter to continue: "
                    )
                ).strip()
                if removal:
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
        # Remove spaces and split by commas.
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
        # Do not print the full listing automatically after file toggles.
    return sorted(selected_files)


def main():
    file_paths = traverse_and_select_files()
    # Finish by printing all selected file paths.
    if file_paths:
        print(colors.yellow("\nFinal Selected Files:"))
        for path in file_paths:
            print(path)
    else:
        print(colors.red("No files were selected."))


if __name__ == "__main__":
    main()
