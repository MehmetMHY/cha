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

    def magenta(self, s):
        return f"\033[95m{s}\033[0m"


colors = Colors()


def print_commands():
    print(colors.red("Commands List:"))
    cmds = [
        "- cd <index>         : Enter a directory by its index (directories are listed first).",
        "- cd <dir_name>      : Enter a directory by its name.",
        "- cd ..              : Go up one directory.",
        "- cd -               : Go back to the previous directory.",
        "- cd                 : Return to the original starting directory.",
        "- ls                 : List current directory contents with external selected files (above).",
        "- Enter file number(s) (e.g. 1,2,3 or 1-3): Toggle file selection (only files are toggled).",
        "- done               : Finish selection (also triggered on CTRL-C/CTRL-D).",
    ]
    for cmd in cmds:
        print(colors.red(cmd))


def print_listing(current_dir, selected_files, prefix_selected=False):
    # When prefix_selected is True (for ls), list only selected files that are not in the current directory.
    if prefix_selected:
        external_selected = sorted(
            [f for f in selected_files if os.path.dirname(f) != current_dir]
        )
        if external_selected:
            print(colors.yellow("Selected files:"))
            for k, path in enumerate(external_selected, start=1):
                print(f"  {k}) {path}")
    print(colors.magenta("Current Directory:"), current_dir)
    # Get directories and files separately and sort them.
    all_entries = os.listdir(current_dir)
    dirs = sorted(
        [e for e in all_entries if os.path.isdir(os.path.join(current_dir, e))],
        key=str.lower,
    )
    files = sorted(
        [e for e in all_entries if os.path.isfile(os.path.join(current_dir, e))],
        key=str.lower,
    )

    index = 1
    # List directories first.
    for d in dirs:
        print(f"  {index}) {colors.blue(d + '/')}")
        index += 1
    # Then list files.
    for f in files:
        full_path = os.path.join(current_dir, f)
        mark = "[x]" if full_path in selected_files else "[ ]"
        print(f"  {index}) {mark} {f}")
        index += 1


def parse_selection_input(selection_input):
    """
    Accepts a string like "1,3,5-7" and returns a list of integers.
    """
    selection_input = selection_input.replace(" ", "")
    indices = []
    parts = selection_input.split(",")
    for part in parts:
        if "-" in part:
            try:
                start_str, end_str = part.split("-", 1)
                start = int(start_str)
                end = int(end_str)
                if start > end:
                    start, end = end, start
                indices.extend(range(start, end + 1))
            except ValueError:
                return None
        else:
            if part.isdigit():
                indices.append(int(part))
            else:
                return None
    return indices


def traverse_and_select_files():
    original_dir = os.getcwd()  # Keep track of the starting directory.
    current_dir = original_dir
    previous_dir = None  # To support "cd -"
    selected_files = set()

    print_commands()
    print_listing(current_dir, selected_files)

    while True:
        try:
            user_input = input(colors.yellow("Enter command: ")).strip()
        except (KeyboardInterrupt, EOFError):
            print()  # Print a blank line to keep output clean.
            break

        # Exit the loop if the user presses Enter without typing a command.
        if user_input == "":
            break

        # If the command is "done" then finish.
        if user_input.lower() == "done":
            break

        tokens = user_input.split()
        cmd = tokens[0].lower()

        if cmd == "cd":
            # If no extra argument is given, go to the original directory.
            if len(tokens) == 1:
                if current_dir != original_dir:
                    previous_dir = current_dir
                    current_dir = original_dir
                print_listing(current_dir, selected_files)
                continue
            # If an argument is provided.
            arg = tokens[1]
            if arg == "..":
                parent = os.path.dirname(current_dir)
                if parent and parent != current_dir:
                    previous_dir = current_dir
                    current_dir = parent
                    print_listing(current_dir, selected_files)
                else:
                    print(colors.red("Already at the top-most directory."))
                continue
            elif arg == "-":
                # Go to the previous directory if available.
                if previous_dir is not None:
                    current_dir, previous_dir = previous_dir, current_dir
                    print_listing(current_dir, selected_files)
                else:
                    print(colors.red("No previous directory to return to."))
                continue
            else:
                # Both digit and string cases are allowed.
                all_entries = os.listdir(current_dir)
                # Get only directories.
                dirs = sorted(
                    [
                        e
                        for e in all_entries
                        if os.path.isdir(os.path.join(current_dir, e))
                    ],
                    key=str.lower,
                )
                if arg.isdigit():
                    idx = int(arg)
                    if 1 <= idx <= len(dirs):
                        chosen = dirs[idx - 1]
                        previous_dir = current_dir
                        current_dir = os.path.join(current_dir, chosen)
                        print_listing(current_dir, selected_files)
                    else:
                        print(colors.red("Directory index out of range."))
                else:
                    if arg in dirs:
                        previous_dir = current_dir
                        current_dir = os.path.join(current_dir, arg)
                        print_listing(current_dir, selected_files)
                    else:
                        print(
                            colors.red(
                                f"Directory '{arg}' not found in current directory."
                            )
                        )
                continue

        # "ls" command: list current contents with external selected files shown above.
        if cmd == "ls":
            print_listing(current_dir, selected_files, prefix_selected=True)
            continue

        # Otherwise, assume file toggle selection input.
        indices = parse_selection_input(user_input)
        if indices is None:
            print(
                colors.red(
                    "Invalid input. Please enter file number(s) separated by commas or ranges like 1-3, or a valid command."
                )
            )
            continue

        # Recompute directories and files in the current directory.
        all_entries = os.listdir(current_dir)
        dirs = sorted(
            [e for e in all_entries if os.path.isdir(os.path.join(current_dir, e))],
            key=str.lower,
        )
        files = sorted(
            [e for e in all_entries if os.path.isfile(os.path.join(current_dir, e))],
            key=str.lower,
        )
        file_start_index = len(dirs) + 1
        file_end_index = file_start_index + len(files) - 1

        for idx in indices:
            if idx < file_start_index or idx > file_end_index:
                print(
                    colors.red(
                        f"Index {idx} is not a valid file selection in this directory."
                    )
                )
                continue
            file_idx = idx - file_start_index  # zero-based index for files.
            filename = files[file_idx]
            full_path = os.path.join(current_dir, filename)
            if full_path in selected_files:
                selected_files.remove(full_path)
                print(colors.yellow(f"Unselected: {full_path}"))
            else:
                selected_files.add(full_path)
                print(colors.green(f"Selected: {full_path}"))
        # No automatic listing is performed after toggling.

    # End of selection loop—final removal prompt.
    if selected_files:
        sorted_sel = sorted(selected_files)
        print(colors.yellow("\nSelected files before finalizing:"))
        for k, path in enumerate(sorted_sel, start=1):
            print(f"  {k}) {path}")
        removal = input(
            colors.yellow(
                "Enter number(s) (e.g. 1,2 or 2-4) to remove from selected files or press Enter to continue: "
            )
        ).strip()
        if removal:
            removal_indices = parse_selection_input(removal)
            if removal_indices is None:
                print(colors.red("Invalid removal input. No files removed."))
            else:
                for r in removal_indices:
                    if 1 <= r <= len(sorted_sel):
                        file_to_remove = sorted_sel[r - 1]
                        if file_to_remove in selected_files:
                            selected_files.remove(file_to_remove)
                            print(colors.yellow(f"Removed: {file_to_remove}"))
                    else:
                        print(colors.red(f"Invalid removal index: {r}"))
    return sorted(selected_files)


def main():
    file_paths = traverse_and_select_files()
    if file_paths:
        print(colors.yellow("\nFinal Selected Files:"))
        for path in file_paths:
            print(path)
    else:
        print(colors.red("No files were selected."))


if __name__ == "__main__":
    main()
