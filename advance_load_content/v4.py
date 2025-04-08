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
        "- cd <index>         : Enter a directory by its index.",
        "- cd <dir_name>      : Enter a directory by its name.",
        "- cd ..              : Go up one directory.",
        "- ls                 : Show the current directory and selected files.",
        "- list               : Show the current directory and selected files without removal prompt.",
        "- Enter file number(s) (e.g. 1,2,3): Toggle file selection (only for files).",
        "- done               : Finish selection (also triggered on CTRL-C/CTRL-D).",
    ]
    for cmd in cmds:
        print(colors.red(cmd))


def print_listing(current_dir, selected_files):
    # Get all entries in the directory and sort them alphabetically (case-insensitive)
    entries = sorted(os.listdir(current_dir), key=lambda s: s.lower())
    print(colors.magenta("Current Directory:"), current_dir)
    for i, entry in enumerate(entries, start=1):
        full_path = os.path.join(current_dir, entry)
        if os.path.isdir(full_path):
            # Directories show as blue with a trailing "/"
            print(f"  {i}) {colors.blue(entry + '/')}")
        elif os.path.isfile(full_path):
            mark = "[x]" if full_path in selected_files else "[ ]"
            # Files printed in default white
            print(f"  {i}) {mark} {entry}")
        else:
            # For any other types of file system entries.
            print(f"  {i}) {entry}")

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

        # If the user types "done", break out of the loop.
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
            # Get unified listing of entries.
            entries = sorted(os.listdir(current_dir), key=lambda s: s.lower())
            # If argument is digit, interpret it as an index.
            if arg.isdigit():
                idx = int(arg)
                if 1 <= idx <= len(entries):
                    chosen_entry = entries[idx - 1]
                    full_path = os.path.join(current_dir, chosen_entry)
                    if os.path.isdir(full_path):
                        current_dir = full_path
                        print_listing(current_dir, selected_files)
                    else:
                        print(colors.red(f"Index {idx} is not a directory."))
                else:
                    print(colors.red("Index out of range."))
            else:
                # Look for a directory with that name.
                if arg in entries:
                    full_path = os.path.join(current_dir, arg)
                    if os.path.isdir(full_path):
                        current_dir = full_path
                        print_listing(current_dir, selected_files)
                    else:
                        print(colors.red(f"'{arg}' is not a directory."))
                else:
                    print(
                        colors.red(f"Directory '{arg}' not found in current directory.")
                    )
            continue

        # "ls" command: simply show current state.
        if tokens and tokens[0].lower() == "ls":
            print_listing(current_dir, selected_files)
            continue

        # "list" command: show listing, but do not prompt for removal.
        if tokens and tokens[0].lower() == "list":
            print_listing(current_dir, selected_files)
            continue

        # Otherwise, assume the input is a file toggle selection.
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

        # Get unified sorted entries.
        entries = sorted(os.listdir(current_dir), key=lambda s: s.lower())
        for idx in chosen_indices:
            if idx < 1 or idx > len(entries):
                print(colors.red(f"Index {idx} is out of range."))
                continue
            entry = entries[idx - 1]
            full_path = os.path.join(current_dir, entry)
            # Only toggle files.
            if os.path.isfile(full_path):
                if full_path in selected_files:
                    selected_files.remove(full_path)
                    print(colors.yellow(f"Unselected: {full_path}"))
                else:
                    selected_files.add(full_path)
                    print(colors.green(f"Selected: {full_path}"))
            else:
                print(
                    colors.red(
                        f"Index {idx} ('{entry}') is not a file and cannot be selected."
                    )
                )
        # Do not auto-print full listing after toggles.
    # End of main loop—before finalizing, ask if the user wants to remove any files from the selection.
    if selected_files:
        sorted_sel = sorted(selected_files)
        print(colors.yellow("\nSelected files before finalizing:"))
        for k, path in enumerate(sorted_sel, start=1):
            print(f"  {k}) {path}")
        removal = input(
            colors.yellow(
                "Enter number(s) (e.g. 1,2) to remove from selected files or press Enter to continue: "
            )
        ).strip()
        if removal:
            removal_indices = removal.replace(" ", "").split(",")
            for r in removal_indices:
                if r.isdigit():
                    rem_idx = int(r)
                    if 1 <= rem_idx <= len(sorted_sel):
                        file_to_remove = sorted_sel[rem_idx - 1]
                        if file_to_remove in selected_files:
                            selected_files.remove(file_to_remove)
                            print(colors.yellow(f"Removed: {file_to_remove}"))
                    else:
                        print(colors.red(f"Invalid removal index: {rem_idx}"))
                else:
                    print(colors.red(f"Invalid input for removal: {r}"))
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
