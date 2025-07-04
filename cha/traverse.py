import subprocess
import os

from cha import colors, config, utils


def collect_files(directory):
    # recursively collect selectable files from a directory
    gathered: list[str] = []

    # normalize DIRS_TO_IGNORE and remove trailing slashes
    ignored_dir_names = {
        d.strip(os.sep) for d in config.DIRS_TO_IGNORE if d.strip(os.sep)
    }

    for root, dirnames, files in os.walk(directory, topdown=True):
        # prevent os.walk from descending into ignored directories
        dirnames[:] = [d for d in dirnames if d not in ignored_dir_names]

        # safeguard - skip files if root itself is in an ignored directory path
        current_path_segments = set(os.path.normpath(root).split(os.sep))
        if not ignored_dir_names.isdisjoint(current_path_segments):
            continue  # skip files in this root

        for name in files:
            ext = os.path.splitext(name)[1].lower()
            # check against binary extensions and specific files to ignore
            if ext in config.BINARY_EXTENSIONS or name in config.FILES_TO_IGNORE:
                continue
            gathered.append(os.path.join(root, name))

    return gathered


def print_help():
    return utils.rls(
        """
        cd       : Navigate directories using fzf (includes ".." to go back)
        select   : Select multiple files/dirs in current directory (use TAB to multi-select)
        unselect : Remove files from current selection (use TAB to multi-select)
        help     : Show this help message
        exit     : Exit the file selection interface
        """
    )


def run_fzf(items, prompt="", multi_select=False, header=""):
    """Run fzf with the given items and return selected items."""
    if not items:
        return []

    fzf_input = "\n".join(items)
    fzf_args = ["fzf"]

    if multi_select:
        fzf_args.append("-m")

    if prompt:
        fzf_args.extend(["--prompt", prompt])

    if header:
        fzf_args.extend(["--header", header])

    try:
        fzf_process = subprocess.run(
            fzf_args,
            input=fzf_input,
            capture_output=True,
            text=True,
            check=True,
            encoding="utf-8",
        )
        result = fzf_process.stdout.strip()
        if result:
            return result.split("\n")
        return []
    except FileNotFoundError:
        print(colors.red("fzf not found. Please install fzf to use this feature."))
        return []
    except subprocess.CalledProcessError:
        # User cancelled fzf (pressed Escape or Ctrl+C)
        print(colors.yellow("Selection cancelled."))
        return []


def cd_command(current_dir, root_dir):
    """Navigate directories using fzf."""
    try:
        entries = os.listdir(current_dir)
        dirs = [
            d
            for d in entries
            if os.path.isdir(os.path.join(current_dir, d))
            and d + "/" not in config.DIRS_TO_IGNORE
            and d not in config.DIRS_TO_IGNORE
        ]

        # Always add ".." unless we're at filesystem root
        options = []
        parent_dir = os.path.dirname(current_dir)
        if parent_dir != current_dir:  # Not at filesystem root
            options.append("..")
        options.extend(sorted(dirs, key=str.lower))

        if not options:
            print(colors.yellow("No directories to navigate to."))
            return current_dir

        selected = run_fzf(
            options,
            prompt="Navigate to> ",
            header="Select directory to navigate to (.. = go back)",
        )

        if selected:
            choice = selected[0]
            if choice == "..":
                return parent_dir
            else:
                new_dir = os.path.join(current_dir, choice)
                if os.path.isdir(new_dir):
                    return new_dir
                else:
                    print(colors.red(f"Directory '{choice}' not found."))

        return current_dir

    except Exception as e:
        print(colors.red(f"Error navigating: {e}"))
        return current_dir


def select_command(current_dir, selected_files):
    """Select files/dirs in current directory using fzf."""
    try:
        entries = os.listdir(current_dir)
        dirs = [
            d + "/"
            for d in entries
            if os.path.isdir(os.path.join(current_dir, d))
            and d + "/" not in config.DIRS_TO_IGNORE
            and d not in config.DIRS_TO_IGNORE
        ]
        files = [
            f
            for f in entries
            if os.path.isfile(os.path.join(current_dir, f))
            and f not in config.FILES_TO_IGNORE
        ]

        options = sorted(dirs + files, key=str.lower)

        if not options:
            print(colors.yellow("No files or directories to select."))
            return selected_files

        selected = run_fzf(
            options,
            prompt="Select files/dirs> ",
            multi_select=True,
            header="Use TAB to select/deselect multiple items, ENTER to confirm",
        )

        if selected:
            for item in selected:
                if item.endswith("/"):
                    # Directory - select all files in it
                    dir_name = item[:-1]
                    dir_path = os.path.join(current_dir, dir_name)
                    dir_files = collect_files(dir_path)
                    for file_path in dir_files:
                        selected_files.add(file_path)
                else:
                    # File
                    file_path = os.path.join(current_dir, item)
                    selected_files.add(file_path)

        return selected_files

    except Exception as e:
        print(colors.red(f"Error selecting files: {e}"))
        return selected_files


def unselect_command(selected_files):
    """Remove files from current selection using fzf."""
    if not selected_files:
        print(colors.yellow("No files currently selected."))
        return selected_files

    try:
        options = sorted(list(selected_files))

        selected = run_fzf(
            options,
            prompt="Unselect files> ",
            multi_select=True,
            header="Use TAB to select files to REMOVE from selection, ENTER to confirm",
        )

        if selected:
            for item in selected:
                if item in selected_files:
                    selected_files.remove(item)

        return selected_files

    except Exception as e:
        print(colors.red(f"Error unselecting files: {e}"))
        return selected_files


def traverse_and_select_files():
    """Main interface for file selection."""
    root_dir = os.getcwd()
    current_dir = root_dir
    selected_files = set()

    print(colors.magenta(print_help()))

    while True:
        try:
            header_line = (
                colors.red(f"[{len(selected_files)}]") + " " + colors.green(current_dir)
            )
            print(header_line)
            user_input = input(colors.yellow(colors.bold(">>> "))).strip().lower()

            if not user_input or user_input in {"exit", "quit"}:
                break
            elif user_input in {"help", "--help", "-h"}:
                print(colors.magenta(print_help()))
                continue
            elif user_input == "cd":
                current_dir = cd_command(current_dir, root_dir)
            elif user_input == "select":
                selected_files = select_command(current_dir, selected_files)
            elif user_input == "unselect":
                selected_files = unselect_command(selected_files)
            else:
                print(colors.red(f"Unknown command: {user_input}"))
                print(colors.red("Type 'help' to see available commands."))

        except (KeyboardInterrupt, EOFError):
            print()
            break
        except Exception as e:
            print(colors.red(f"Error: {e}"))

    return sorted(list(selected_files))


def msg_content_load(client):
    try:
        from cha import utils, loading

        paths = traverse_and_select_files()
        if not paths:
            return None

        complex_types = (
            config.SUPPORTED_AUDIO_FORMATS
            + config.SUPPORTED_IMG_FORMATS
            + config.SUPPORTED_VIDEO_FORMATS
        )
        needs_spinner = any(
            os.path.splitext(p)[1].lower() in complex_types for p in paths
        )
        if needs_spinner:
            loading.start_loading("Loading files", "rectangles")

        contents: list[tuple[str, str]] = []
        try:
            for p in paths:
                c = utils.load_most_files(
                    client=client,
                    file_path=p,
                    model_name=config.CHA_DEFAULT_IMAGE_MODEL,
                    prompt=None,
                )
                contents.append((p, c))
        finally:
            if needs_spinner:
                loading.stop_loading()

        return "\n".join(
            f"CONTENT FOR {p}:\n``````````\n{c}\n``````````\n" for p, c in contents
        )
    except (KeyboardInterrupt, EOFError):
        print()
        return None
    except Exception as exc:
        print(colors.red(f"Error during traverse: {exc}"))
        return None
