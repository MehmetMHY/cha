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


def get_traverse_help_options():
    help_options = []
    help_options.append("[ALL] - show all help options")
    help_options.append(
        '[c] cd - navigate directories using fzf (includes ".." to go back)'
    )
    help_options.append(
        "[s] select - select multiple files/dirs in current directory (use tab to multi-select)"
    )
    help_options.append(
        "[u] unselect - remove files from current selection (use tab to multi-select)"
    )
    help_options.append(
        "[l] ls - list all contents in current directory [-f: files | -d: dirs]"
    )
    help_options.append(
        "[v] view - open a file in text editor using terminal loading logic"
    )
    help_options.append("[h] help - show this help message")
    help_options.append("[e] exit - exit the file selection interface")
    return help_options


def interactive_traverse_help():
    help_options = get_traverse_help_options()

    try:
        selected_output = utils.run_fzf_ssh_safe(
            [
                "fzf",
                "--reverse",
                "--height=40%",
                "--border",
                "--prompt=select help option, enter to confirm, esc to cancel: ",
                "--exact",
            ],
            "\n".join(help_options),
        )
        if selected_output:
            selected_item = selected_output.strip()

            if "[ALL]" in selected_item:
                for help_item in help_options:
                    if "[ALL]" not in help_item:
                        print(colors.yellow(help_item))
                return None

            # check if this is an executable command
            if "[v] view" in selected_item:
                return "v"
            elif "[c] cd" in selected_item:
                return "c"
            elif "[s] select" in selected_item:
                return "s"
            elif "[u] unselect" in selected_item:
                return "u"
            elif "[l] ls" in selected_item:
                return "l"
            elif "[e] exit" in selected_item:
                return "e"

            # just print the selected item
            print(colors.yellow(selected_item))
            return None

    except (subprocess.CalledProcessError, subprocess.SubprocessError):
        pass

    return None


def print_help():
    return utils.rls(
        """
        [c] cd       : Navigate directories using fzf (includes ".." to go back)
        [s] select   : Select multiple files/dirs in current directory (use TAB to multi-select)
        [u] unselect : Remove files from current selection (use TAB to multi-select)
        [l] ls       : List all contents in current directory [-f: files | -d: dirs]
        [v] view     : Open a file in text editor using terminal loading logic
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
        from cha import utils

        result = utils.run_fzf_ssh_safe(fzf_args, fzf_input)
        if result:
            return result.split("\n")
        return []
    except FileNotFoundError:
        print(colors.red("Please install fzf!"))
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
                print(colors.red(f"Could not find {target_name}"))
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
                    print(colors.red(f"Could not find path: {target_name}"))
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
                    print(colors.red(f"Failed to find {target_name}"))
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


def view_command(current_dir, target_name=None):
    """open a file in text editor with terminal loading logic"""
    try:
        from cha import loading

        if target_name:
            if target_name.startswith("./"):
                relative_path = target_name[2:]
                file_path = os.path.join(current_dir, relative_path)
            else:
                file_path = os.path.join(current_dir, target_name)

            if os.path.exists(file_path) and os.path.isfile(file_path):
                success = utils.open_file_in_editor(file_path)
                if not success:
                    print(colors.red("no text editor available"))
                return
            else:
                print(colors.red(f"file '{target_name}' not found or is not a file"))
                return

        # if no target specified, let user select from files in current directory
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

        files = [
            f
            for f in entries
            if os.path.isfile(os.path.join(current_dir, f))
            and f not in config.FILES_TO_IGNORE
        ]

        if not files:
            print(colors.yellow("no files to view in current directory"))
            return

        files.sort(key=str.lower)

        # format paths for better fzf display
        full_paths = [os.path.join(current_dir, f) for f in files]
        formatted_paths, path_mapping = utils.format_paths_for_fzf(full_paths)

        selected = run_fzf(
            formatted_paths,
            prompt="select file to view> ",
            header="select a file to open in text editor",
        )

        if selected:
            # convert back to actual path
            actual_paths = utils.extract_paths_from_fzf_selection(
                selected, path_mapping
            )
            if actual_paths:
                file_path = actual_paths[0]
                success = utils.open_file_in_editor(file_path)
                if not success:
                    print(colors.red("no text editor available"))

    except Exception as e:
        print(colors.red(f"error viewing file: {e}"))


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

            user_input = input(colors.blue(colors.bold(">>> "))).strip()
            user_input_lower = user_input.lower()

            if not user_input or user_input_lower in {"exit", "quit", "e"}:
                break
            elif user_input_lower in {"help", "--help", "-h", "h"}:
                selected_command = interactive_traverse_help()
                if selected_command:
                    # continue processing in the main loop without consuming this iteration
                    if selected_command == "e":
                        break
                    elif selected_command == "c":
                        current_dir = cd_command(current_dir, root_dir)
                    elif selected_command == "s":
                        selected_files = select_command(current_dir, selected_files)
                    elif selected_command == "u":
                        selected_files = unselect_command(selected_files)
                    elif selected_command == "l":
                        ls_command(current_dir)
                    elif selected_command == "v":
                        view_command(current_dir)
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
                            print(colors.yellow(f"Ignoring directory {dir_name}"))
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
            elif user_input_lower.startswith("view ") or user_input_lower.startswith(
                "v "
            ):
                parts = user_input.split(maxsplit=1)
                target_name = parts[1].strip() if len(parts) > 1 else None
                view_command(current_dir, target_name)
            elif user_input_lower in {"view", "v"}:
                view_command(current_dir)
            else:
                print(colors.red("Type 'help' to see available commands"))

        except (KeyboardInterrupt, EOFError):
            print()
            break
        except Exception as e:
            print(colors.red(f"{e}"))

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
