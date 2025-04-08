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
        "- ls                 : Show current directory and external selected files (displayed above).",
        "- list               : Show the current directory without printing any selected files list.",
        "- Enter file number(s) (e.g. 1,2,3 or 1-3): Toggle file selection (only files can be toggled).",
        "- done               : Finish selection (also triggered on CTRL-C/CTRL-D).",
    ]
    for cmd in cmds:
        print(colors.red(cmd))


def print_listing(current_dir, selected_files, prefix_selected=False):
    # If prefix_selected is True (as in ls), list only those selected files which are not in the current directory,
    # and show them above the content listing.
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
                # Allow selection in either order.
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
    current_dir = os.getcwd()
    selected_files = set()
    print_commands()
    # Initial listing (default mode – without any "Selected files:" printed).
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
            # Get directories only.
            all_entries = os.listdir(current_dir)
            dirs = sorted(
                [e for e in all_entries if os.path.isdir(os.path.join(current_dir, e))],
                key=str.lower,
            )
            # If numeric argument then it must correspond to a directory.
            if arg.isdigit():
                idx = int(arg)
                if 1 <= idx <= len(dirs):
                    chosen = dirs[idx - 1]
                    current_dir = os.path.join(current_dir, chosen)
                    print_listing(current_dir, selected_files)
                else:
                    print(colors.red("Directory index out of range."))
            else:
                # Treat arg as directory name.
                if arg in dirs:
                    current_dir = os.path.join(current_dir, arg)
                    print_listing(current_dir, selected_files)
                else:
                    print(
                        colors.red(f"Directory '{arg}' not found in current directory.")
                    )
            continue

        # "ls" command: list current contents with external selected files printed above.
        if tokens and tokens[0].lower() == "ls":
            print_listing(current_dir, selected_files, prefix_selected=True)
            continue

        # "list" command: list current contents without printing any "Selected files:" section.
        if tokens and tokens[0].lower() == "list":
            print_listing(current_dir, selected_files)
            continue

        # Otherwise, assume the input is for file toggle selection.
        indices = parse_selection_input(user_input)
        if indices is None:
            print(
                colors.red(
                    "Invalid input. Please enter file number(s) separated by commas (or ranges like 1-3), or a valid command."
                )
            )
            continue

        # Recompute directories and files.
        all_entries = os.listdir(current_dir)
        dirs = sorted(
            [e for e in all_entries if os.path.isdir(os.path.join(current_dir, e))],
            key=str.lower,
        )
        files = sorted(
            [e for e in all_entries if os.path.isfile(os.path.join(current_dir, e))],
            key=str.lower,
        )
        # Files come after directories.
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
            file_idx = idx - file_start_index  # zero-based index for files
            filename = files[file_idx]
            full_path = os.path.join(current_dir, filename)
            if full_path in selected_files:
                selected_files.remove(full_path)
                print(colors.yellow(f"Unselected: {full_path}"))
            else:
                selected_files.add(full_path)
                print(colors.green(f"Selected: {full_path}"))
        # Do not automatically print listing after toggling; user can issue ls or list commands.

    # End of selection loop—ask for removal adjustments.
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
    # Final output.
    if file_paths:
        print(colors.yellow("\nFinal Selected Files:"))
        for path in file_paths:
            print(path)
    else:
        print(colors.red("No files were selected."))


if __name__ == "__main__":
    main()
