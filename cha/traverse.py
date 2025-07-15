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

        # safeguard skip files if root itself is in an ignored directory path
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
        [c] cd       : Navigate directories using fzf (includes ".." to go back)
        [s] select   : Select multiple files/dirs in current directory (use TAB to multi-select)
        [u] unselect : Remove files from current selection (use TAB to multi-select)
        [l] ls       : List all contents in current directory [-f: files | -d: dirs]
        [h] help     : Show this help message
        [e] exit     : Exit the file selection interface
        """
    )


def run_fzf(items, prompt="", multi_select=False, header=""):
    """Run fzf with the given items and return selected items"""
    if not items:
        return []

    fzf_input = "\n".join(items)
    fzf_args = ["fzf", "--reverse", "--height=40%", "--border"]

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
        print(colors.red("fzf not found. Please install fzf to use this feature!"))
        return []
    except subprocess.CalledProcessError:
        return []


def cd_command(current_dir, root_dir):
    """Navigate directories using fzf"""
    try:
        entries = []
        for entry in os.listdir(current_dir):
            entries.append(entry)

        try:
            import glob

            hidden_items = glob.glob(os.path.join(current_dir, ".*"))
            for hidden_path in hidden_items:
                hidden_name = os.path.basename(hidden_path)
                if hidden_name not in entries and hidden_name not in [".", ".."]:
                    entries.append(hidden_name)
        except:
            pass

        dirs = [
            d
            for d in entries
            if os.path.isdir(os.path.join(current_dir, d))
            and d + "/" not in config.DIRS_TO_IGNORE
            and d not in config.DIRS_TO_IGNORE
        ]

        # always add ".." unless we're at filesystem root
        options = []
        parent_dir = os.path.dirname(current_dir)
        if parent_dir != current_dir:  # Not at filesystem root
            options.append("..")
        options.extend(sorted(dirs, key=str.lower))

        if not options:
            print(colors.yellow("No directories to navigate to"))
            return current_dir

        # format paths for better fzf display (except for "..")
        formatted_options = []
        path_mapping = {}

        for option in options:
            if option == "..":
                formatted_options.append(option)
                path_mapping[option] = option
            else:
                full_path = os.path.join(current_dir, option)
                formatted = utils.format_path_for_fzf(full_path)
                formatted_options.append(formatted)
                path_mapping[formatted] = option

        selected = run_fzf(
            formatted_options,
            prompt="Navigate to> ",
            header="Select directory to navigate to (.. = go back)",
        )

        if selected:
            choice_formatted = selected[0]
            choice = path_mapping.get(choice_formatted, choice_formatted)

            if choice == "..":
                return parent_dir
            else:
                new_dir = os.path.join(current_dir, choice)
                if os.path.isdir(new_dir):
                    return new_dir
                else:
                    print(colors.red(f"Directory '{choice}' not found"))

        return current_dir

    except Exception as e:
        print(colors.red(f"Error navigating: {e}"))
        return current_dir


def select_command(current_dir, selected_files, target_name=None):
    """Select files/dirs in current directory using fzf or direct name"""
    try:
        entries = []
        for entry in os.listdir(current_dir):
            entries.append(entry)

        try:
            import glob

            hidden_items = glob.glob(os.path.join(current_dir, ".*"))
            for hidden_path in hidden_items:
                hidden_name = os.path.basename(hidden_path)
                if hidden_name not in entries and hidden_name not in [".", ".."]:
                    entries.append(hidden_name)
        except:
            pass

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
            print(colors.yellow("No files or directories to select"))
            return selected_files

        if target_name:
            if target_name.startswith("./"):
                relative_path = target_name[2:]
                full_path = os.path.join(current_dir, relative_path)
                if os.path.exists(full_path):
                    if os.path.isfile(full_path):
                        selected_files.add(full_path)
                        return selected_files
                    elif os.path.isdir(full_path):
                        dir_files = collect_files(full_path)
                        for file_path in dir_files:
                            selected_files.add(file_path)
                        return selected_files
                else:
                    print(colors.red(f"Path '{target_name}' not found"))
                    return selected_files
            elif target_name in files:
                file_path = os.path.join(current_dir, target_name)
                selected_files.add(file_path)
                return selected_files
            elif target_name + "/" in dirs:
                dir_path = os.path.join(current_dir, target_name)
                dir_files = collect_files(dir_path)
                for file_path in dir_files:
                    selected_files.add(file_path)
                return selected_files
            else:
                print(colors.red(f"File or directory '{target_name}' not found"))
                return selected_files

        # create full paths for formatting
        full_paths = []
        for item in options:
            if item.endswith("/"):
                dir_name = item[:-1]
                full_paths.append(os.path.join(current_dir, dir_name))
            else:
                full_paths.append(os.path.join(current_dir, item))

        # format paths for better fzf display
        formatted_paths, path_mapping = utils.format_paths_for_fzf(full_paths)

        selected = run_fzf(
            formatted_paths,
            prompt="Select files/dirs> ",
            multi_select=True,
            header="Use TAB to select/deselect multiple items, ENTER to confirm",
        )

        if selected:
            # convert back to actual paths
            actual_paths = utils.extract_paths_from_fzf_selection(
                selected, path_mapping
            )
            for full_path in actual_paths:
                if os.path.isdir(full_path):
                    dir_files = collect_files(full_path)
                    for file_path in dir_files:
                        selected_files.add(file_path)
                else:
                    selected_files.add(full_path)

        return selected_files

    except Exception as e:
        print(colors.red(f"Error selecting files: {e}"))
        return selected_files


def unselect_command(selected_files, target_name=None):
    """Remove files from current selection using fzf or direct name"""
    if not selected_files:
        print(colors.yellow("No files currently selected"))
        return selected_files

    try:
        options = sorted(list(selected_files))

        if target_name:
            if target_name.startswith("./"):
                relative_path = target_name[2:]
                full_path = os.path.join(os.getcwd(), relative_path)
                full_path = os.path.abspath(full_path)
                if full_path in selected_files:
                    selected_files.remove(full_path)
                    return selected_files
                else:
                    print(colors.red(f"Path '{target_name}' not found in selection"))
                    return selected_files
            else:
                matching_files = [
                    f for f in selected_files if os.path.basename(f) == target_name
                ]
                if matching_files:
                    for file_path in matching_files:
                        selected_files.remove(file_path)
                    return selected_files
                else:
                    print(colors.red(f"File '{target_name}' not found in selection"))
                    return selected_files

        # format paths for better fzf display
        formatted_paths, path_mapping = utils.format_paths_for_fzf(options)

        selected = run_fzf(
            formatted_paths,
            prompt="Unselect files> ",
            multi_select=True,
            header="Use TAB to select files to REMOVE from selection, ENTER to confirm",
        )

        if selected:
            # convert back to actual paths and remove them
            actual_paths = utils.extract_paths_from_fzf_selection(
                selected, path_mapping
            )
            for path in actual_paths:
                if path in selected_files:
                    selected_files.remove(path)

        return selected_files

    except Exception as e:
        print(colors.red(f"Error unselecting files: {e}"))
        return selected_files


def ls_command(current_dir, flag=None):
    """List all contents in the current directory"""
    try:
        entries = []
        for entry in os.listdir(current_dir):
            entries.append(entry)

        try:
            import glob

            hidden_items = glob.glob(os.path.join(current_dir, ".*"))
            for hidden_path in hidden_items:
                hidden_name = os.path.basename(hidden_path)
                if hidden_name not in entries and hidden_name not in [".", ".."]:
                    entries.append(hidden_name)
        except:
            pass

        dirs = []
        files = []

        for entry in entries:
            entry_path = os.path.join(current_dir, entry)
            if os.path.isdir(entry_path):
                dirs.append(entry + "/")
            else:
                files.append(entry)

        dirs.sort(key=str.lower)
        files.sort(key=str.lower)

        if flag == "-f":
            all_items = files
        elif flag == "-d":
            all_items = dirs
        else:
            all_items = dirs + files

        if not all_items:
            print(colors.yellow("Directory is empty"))
        else:
            for item in all_items:
                print(item)

    except Exception as e:
        print(colors.red(f"Error listing directory: {e}"))


def traverse_and_select_files():
    """Main interface for file selection"""
    root_dir = os.getcwd()
    current_dir = root_dir
    selected_files = set()

    # Track previous state to only show changes
    prev_dir = None
    prev_selected_count = -1

    print(colors.cyan("Type 'help' for command options"))

    while True:
        try:
            # Only show directory/count if something changed
            if current_dir != prev_dir or len(selected_files) != prev_selected_count:
                header_line = (
                    colors.red(f"[{len(selected_files)}]")
                    + " "
                    + colors.green(current_dir)
                )
                print(header_line)
                prev_dir = current_dir
                prev_selected_count = len(selected_files)

            user_input = input(colors.yellow(colors.bold(">>> "))).strip()
            user_input_lower = user_input.lower()

            if not user_input or user_input_lower in {"exit", "quit", "e"}:
                break
            elif user_input_lower in {"help", "--help", "-h", "h"}:
                print(colors.magenta(print_help()))
                continue
            elif user_input == "cd ..":
                parent_dir = os.path.dirname(current_dir)
                if parent_dir != current_dir:
                    current_dir = parent_dir
            elif user_input_lower.startswith("cd ") or user_input_lower.startswith(
                "c "
            ):
                parts = user_input.split(maxsplit=1)
                dir_name = parts[1].strip() if len(parts) > 1 else ""

                if dir_name == "..":
                    parent_dir = os.path.dirname(current_dir)
                    if parent_dir != current_dir:
                        current_dir = parent_dir
                elif dir_name:
                    target_dir = os.path.join(current_dir, dir_name)
                    if os.path.isdir(target_dir):
                        if (
                            dir_name + "/" not in config.DIRS_TO_IGNORE
                            and dir_name not in config.DIRS_TO_IGNORE
                        ):
                            current_dir = target_dir
                        else:
                            print(colors.yellow(f"Directory '{dir_name}' is ignored"))
            elif user_input_lower in {"cd", "c"}:
                current_dir = cd_command(current_dir, root_dir)
            elif user_input_lower.startswith("select ") or user_input_lower.startswith(
                "s "
            ):
                parts = user_input.split(maxsplit=1)
                target_name = parts[1].strip() if len(parts) > 1 else None
                selected_files = select_command(
                    current_dir, selected_files, target_name
                )
            elif user_input_lower in {"select", "s"}:
                selected_files = select_command(current_dir, selected_files)
            elif user_input_lower.startswith(
                "unselect "
            ) or user_input_lower.startswith("u "):
                parts = user_input.split(maxsplit=1)
                target_name = parts[1].strip() if len(parts) > 1 else None
                selected_files = unselect_command(selected_files, target_name)
            elif user_input_lower in {"unselect", "u"}:
                selected_files = unselect_command(selected_files)
            elif user_input_lower.startswith("ls ") or user_input_lower.startswith(
                "l "
            ):
                parts = user_input.split()
                flag = parts[1] if len(parts) > 1 else None
                ls_command(current_dir, flag)
            elif user_input_lower in {"ls", "l"}:
                ls_command(current_dir)
            else:
                print(colors.red("Type 'help' to see available commands"))

        except (KeyboardInterrupt, EOFError):
            print()
            break
        except Exception as e:
            print(colors.red(f"Error: {e}"))

    return sorted(list(selected_files))


def simple_file_select(single_file=False):
    current_dir = os.getcwd()

    try:
        entries = []
        for entry in os.listdir(current_dir):
            entries.append(entry)

        try:
            import glob

            hidden_files = glob.glob(os.path.join(current_dir, ".*"))
            for hidden_path in hidden_files:
                hidden_name = os.path.basename(hidden_path)
                if os.path.isfile(hidden_path) and hidden_name not in entries:
                    entries.append(hidden_name)
        except:
            pass

        files = [
            f
            for f in entries
            if os.path.isfile(os.path.join(current_dir, f))
            and f not in config.FILES_TO_IGNORE
        ]

        if not files:
            print(colors.yellow("No files found in current directory"))
            return []

        files.sort(key=str.lower)

        selected = run_fzf(
            files,
            prompt="Select file> " if single_file else "Select files> ",
            multi_select=not single_file,
            header=(
                "Select a file to edit, ESC to exit or create new file"
                if single_file
                else "Use TAB to select/deselect multiple files, ENTER to confirm"
            ),
        )

        if selected:
            return [os.path.join(current_dir, f) for f in selected]
        return []

    except Exception as e:
        print(colors.red(f"Error selecting files: {e}"))
        return []


def msg_content_load(client, simple=False, return_path_only=False):
    try:
        from cha import utils, loading

        if simple:
            paths = simple_file_select(single_file=return_path_only)
        else:
            paths = traverse_and_select_files()

        if not paths:
            return None

        if return_path_only:
            return paths[0] if paths else None

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
