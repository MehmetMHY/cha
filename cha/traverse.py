import os

from cha import colors, config


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


def print_commands():
    from cha import utils

    print(
        colors.red(
            utils.rls(
                """
                cd <index|dir_name>   : change directory
                cd .. / cd            : up / back to root
                ls                    : list directory & selections
                <n> or 1,3-5          : toggle file(s) by index
                <dir-index>           : toggle ALL files in that directory
                help / exit           : this help / quit
                edit                  : deselect files from current selection
                clear                 : clear terminal screen
                """
            )
        )
    )


def _dir_selected_mark(dir_path, selected):
    # return [x] if any file inside *dir_path* is selected, else [ ]
    for f in selected:
        if f.startswith(dir_path + os.sep):
            return "[x]"
    return "[ ]"


def print_listing(current_dir, selected, *, show_external=False):
    # pretty list of current dir with selection markers
    if show_external and selected:
        print(colors.yellow("Selected files:"))
        for k, path in enumerate(sorted(selected), 1):
            print(f"   {k}) {path}")

    print(colors.magenta(f"{current_dir}/"))

    entries = os.listdir(current_dir)
    dirs = sorted(
        [
            e
            for e in entries
            if os.path.isdir(os.path.join(current_dir, e))
            and e + "/" not in config.DIRS_TO_IGNORE
            and e not in config.DIRS_TO_IGNORE
        ],
        key=str.lower,
    )
    files = sorted(
        [e for e in entries if os.path.isfile(os.path.join(current_dir, e))],
        key=str.lower,
    )

    idx = 1
    for d in dirs:
        dir_path = os.path.join(current_dir, d)
        print(
            f"   {idx}) {_dir_selected_mark(dir_path, selected)} {colors.blue(d + '/')}"
        )
        idx += 1
    for f in files:
        file_path = os.path.join(current_dir, f)
        mark = "[x]" if file_path in selected else "[ ]"
        print(f"   {idx}) {mark} {f}")
        idx += 1


def parse_selection_input(text):
    # return the list of numeric indices contained in *text* (e.g. "1,3-5")
    text = text.replace(" ", "")
    if not text:
        return None

    out: list[int] = []
    for part in text.split(","):
        if "-" in part:
            try:
                a, b = map(int, part.split("-", 1))
            except ValueError:
                return None
            if a > b:
                a, b = b, a
            out.extend(range(a, b + 1))
        elif part.isdigit():
            out.append(int(part))
        else:
            return None
    return out


def traverse_and_select_files():
    maybe_prompt = None
    root_dir = os.getcwd()
    curr_dir = root_dir
    selected = set()

    print_listing(curr_dir, selected)

    while True:
        try:
            user = input(colors.yellow(colors.bold(">>> "))).strip()
        except (KeyboardInterrupt, EOFError):
            print()
            break

        if user == "" or user.lower() in {"exit", "quit"}:
            break
        if user.lower() in {"help", "--help", "-h"}:
            print_commands()
            continue

        # free-form prompt, if we already have selections
        if (
            not (
                user.startswith("cd")
                or user.startswith("ls")
                or user.startswith("edit")
                or user.replace(" ", "").replace(",", "").replace("-", "").isdigit()
            )
            and selected
        ):
            maybe_prompt = user
            break

        tokens = user.split()
        cmd = tokens[0].lower()

        if cmd == "cd":
            if len(tokens) == 1:
                curr_dir = root_dir
                print_listing(curr_dir, selected)
                continue

            arg = tokens[1]
            if arg == "..":
                curr_dir = os.path.dirname(curr_dir) or curr_dir
                print_listing(curr_dir, selected)
                continue

            entries = os.listdir(curr_dir)
            dirs = sorted(
                [
                    e
                    for e in entries
                    if os.path.isdir(os.path.join(curr_dir, e))
                    and e + "/" not in config.DIRS_TO_IGNORE
                    and e not in config.DIRS_TO_IGNORE
                ],
                key=str.lower,
            )

            # cd by *index*
            if arg.isdigit():
                idx = int(arg)
                if 1 <= idx <= len(dirs):
                    curr_dir = os.path.join(curr_dir, dirs[idx - 1])
                    print_listing(curr_dir, selected)
                else:
                    print(colors.red("Directory index out of range."))
                continue

            # cd by *name*
            if arg in dirs:
                curr_dir = os.path.join(curr_dir, arg)
                print_listing(curr_dir, selected)
            else:
                print(colors.red(f"Directory '{arg}' not found."))
            continue

        if cmd == "ls":
            print_listing(curr_dir, selected, show_external=True)
            continue

        elif cmd.strip().lower() == "clear":
            os.system("clear")
            print_listing(curr_dir, selected, show_external=True)
            continue

        elif cmd == "edit":
            if not selected:
                print(colors.yellow("No files selected to edit/deselect."))
                continue

            while True:
                selected_list_current_round = sorted(list(selected))
                if not selected_list_current_round:
                    print(colors.yellow("All files have been deselected."))
                    break

                print(colors.magenta("Currently selected files (for deselection):"))
                for k, p in enumerate(selected_list_current_round, 1):
                    print(f"   {k}) {p}")

                try:
                    deselection_prompt_text = colors.magenta(
                        "Enter numbers to deselect, or EXIT/DONE to finish deselection: "
                    )
                    user_deselection_input = input(deselection_prompt_text).strip()

                    if (
                        not user_deselection_input
                        or user_deselection_input.lower() == "exit"
                        or user_deselection_input.lower() == "done"
                    ):
                        break

                    indices_to_deselect = parse_selection_input(user_deselection_input)

                    if indices_to_deselect:
                        unique_indices = sorted(list(set(indices_to_deselect)))
                        for idx_deselect in unique_indices:
                            if 1 <= idx_deselect <= len(selected_list_current_round):
                                file_to_deselect = selected_list_current_round[
                                    idx_deselect - 1
                                ]
                                if file_to_deselect in selected:
                                    selected.remove(file_to_deselect)
                                    print(colors.red(f"Deselected: {file_to_deselect}"))
                            else:
                                print(
                                    colors.red(
                                        f"Index {idx_deselect} is out of range for current selection."
                                    )
                                )
                    else:
                        print(
                            colors.red(
                                "Invalid input for deselection. Please enter numbers, ranges, or EXIT/DONE."
                            )
                        )

                except (KeyboardInterrupt, EOFError):
                    print()
                    break
            print_listing(curr_dir, selected)  # show updated listing
            continue

        # numeric / numeric range selection
        indices = parse_selection_input(user)
        if indices is None:
            continue

        entries = os.listdir(curr_dir)
        dirs = sorted(
            [
                e
                for e in entries
                if os.path.isdir(os.path.join(curr_dir, e))
                and e + "/" not in config.DIRS_TO_IGNORE
                and e not in config.DIRS_TO_IGNORE
            ],
            key=str.lower,
        )
        files = sorted(
            [e for e in entries if os.path.isfile(os.path.join(curr_dir, e))],
            key=str.lower,
        )
        file_start = len(dirs) + 1
        file_end = file_start + len(files) - 1

        for idx in indices:
            if 1 <= idx <= len(dirs):
                chosen = dirs[idx - 1]
                dir_path = os.path.join(curr_dir, chosen)
                dir_files = collect_files(dir_path)

                if not dir_files:
                    print(colors.yellow(f"No selectable files found in {dir_path}"))
                    continue

                # toggle: if *all* are selected -> unselect, else select missing
                if dir_files and all(f in selected for f in dir_files):
                    for fp in dir_files:
                        selected.remove(fp)
                    print(colors.yellow(f"Unselected all in {dir_path}"))
                else:
                    for fp in dir_files:
                        if fp not in selected:
                            selected.add(fp)
                    print(colors.green(f"Selected all in {dir_path}"))
                continue

            if idx < file_start or idx > file_end:
                print(colors.red(f"Index {idx} is not a file selection."))
                continue

            fname = files[idx - file_start]
            full = os.path.join(curr_dir, fname)
            if fname in config.FILES_TO_IGNORE:
                print(colors.yellow(f"Ignoring file: {full}"))
                continue
            if full in selected:
                selected.remove(full)
                print(colors.yellow(f"Unselected: {full}"))
            else:
                selected.add(full)
                print(colors.green(f"Selected: {full}"))

    if selected and maybe_prompt == None:
        pass  # effectively removing the old deselection loop

    return sorted(list(selected)), maybe_prompt


def msg_content_load(client):
    try:
        from cha import utils, loading

        paths, prompt = traverse_and_select_files()
        if not paths:
            return None

        if prompt is None:
            prompt = input(colors.yellow("Additional Prompt: "))

        if prompt.strip() == config.TEXT_EDITOR_INPUT_MODE:
            editor_out = utils.check_terminal_editors_and_edit()
            if editor_out:
                prompt = editor_out
                for line in prompt.rstrip("\n").split("\n"):
                    print(colors.yellow(">"), line)

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
                    prompt=prompt,
                )
                contents.append((p, c))
        finally:
            if needs_spinner:
                loading.stop_loading()

        out = "\n".join(
            f"CONTENT FOR {p}:\n``````````\n{c}\n``````````\n" for p, c in contents
        )
        if prompt:
            out = f"PROMPT: {prompt}\n\n" + out
        return out
    except (KeyboardInterrupt, EOFError):
        print()
        return None
    except Exception as exc:
        print(colors.red(f"Error during traverse: {exc}"))
        return None
