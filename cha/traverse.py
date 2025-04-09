import os
import sys

from cha import colors, utils, scraper


def print_commands():
    print(
        colors.red(
            utils.rls(
                """
                Commands List:
                - cd <index>    : Enter a dir by its index
                - cd <dir_name> : Enter a dir by its name
                - cd ..         : Go back one dir
                - cd            : Return to the original starting dir
                - ls            : List current dir's contents and selected files
                - e.g. 1 or 1-3 : Toggle file selection (only files are toggled)
                - exist         : Exist, also triggered on CTRL-C/D or empty str
                """
            )
        )
    )


def print_listing(current_dir, selected_files, prefix_selected=False):
    # when prefix_selected is True (for ls), list only selected files that are not in the current directory
    if prefix_selected:
        external_selected = sorted(
            [f for f in selected_files if os.path.dirname(f) != current_dir]
        )
        if external_selected:
            print(colors.yellow("Selected files:"))
            for k, path in enumerate(external_selected, start=1):
                print(f"  {k}) {path}")

    print(colors.bold(colors.magenta(f"{current_dir}/")))

    # get directories and files separately and sort them.
    all_entries = os.listdir(current_dir)
    dirs = sorted(
        [e for e in all_entries if os.path.isdir(os.path.join(current_dir, e))],
        key=str.lower,
    )
    files = sorted(
        [e for e in all_entries if os.path.isfile(os.path.join(current_dir, e))],
        key=str.lower,
    )

    # list all current dirs and files
    index = 1
    for d in dirs:
        print(f"  {index}) {colors.blue(d + '/')}")
        index += 1
    for f in files:
        full_path = os.path.join(current_dir, f)
        mark = "[x]" if full_path in selected_files else "[ ]"
        print(f"  {index}) {mark} {f}")
        index += 1


def parse_selection_input(selection_input):
    # accepts a string like "1,3,5-7" and returns a list of integers
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
    original_dir = os.getcwd()
    current_dir = original_dir
    selected_files = set()

    # print_commands()

    print_listing(current_dir, selected_files)

    while True:
        try:
            user_input = input(colors.yellow(colors.bold("> "))).strip()
        except (KeyboardInterrupt, EOFError):
            print()
            break

        if user_input == "" or user_input.strip().lower() == "exist":
            break

        if user_input.strip().lower() in ["help", "--help", "-h", "--h"]:
            print_commands()
            continue

        tokens = user_input.split()
        cmd = tokens[0].lower()

        if cmd == "cd":
            # no extra argument is given, go to the original directory
            if len(tokens) == 1:
                if current_dir != original_dir:
                    current_dir = original_dir
                print_listing(current_dir, selected_files)
                continue

            # additional argument(s) is provided
            arg = tokens[1]
            if arg == "..":
                parent = os.path.dirname(current_dir)
                if parent and parent != current_dir:
                    current_dir = parent
                    print_listing(current_dir, selected_files)
                else:
                    print(colors.red("Already at the top-most directory"))
                continue
            else:
                # both digit and string cases are allowed
                all_entries = os.listdir(current_dir)

                # get only directories.
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
                        current_dir = os.path.join(current_dir, chosen)
                        print_listing(current_dir, selected_files)
                    else:
                        print(colors.red("Directory index out of range."))
                else:
                    if arg in dirs:
                        current_dir = os.path.join(current_dir, arg)
                        print_listing(current_dir, selected_files)
                    else:
                        print(
                            colors.red(
                                f"Directory '{arg}' not found in current directory"
                            )
                        )
                continue

        # list current contents with external selected files shown above
        if cmd == "ls":
            print_listing(current_dir, selected_files, prefix_selected=True)
            continue

        # assume file toggle selection input
        indices = parse_selection_input(user_input)
        if indices is None:
            print(colors.red("Invalid input!"))
            continue

        # recompute directories and files in the current directory
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
                        f"Index {idx} is not a valid file selection in this directory"
                    )
                )
                continue

            # zero-based index for files
            file_idx = idx - file_start_index

            filename = files[file_idx]
            full_path = os.path.join(current_dir, filename)
            if full_path in selected_files:
                selected_files.remove(full_path)
                print(colors.yellow(f"Unselected: {full_path}"))
            else:
                selected_files.add(full_path)
                print(colors.green(f"Selected: {full_path}"))

    # end of selection loop—final removal prompt
    if selected_files:
        sorted_sel = sorted(selected_files)
        print(colors.yellow("Selected files before finalizing:"))
        for k, path in enumerate(sorted_sel, start=1):
            print(f"  {k}) {path}")
        removal = input(
            colors.yellow("Selected files to remove (e.g. 1,2 or 2-4): ")
        ).strip()
        if removal:
            removal_indices = parse_selection_input(removal)
            if removal_indices is None:
                print(colors.red("Invalid removal input, no files removed!"))
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
