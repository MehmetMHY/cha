import subprocess
import os
from pathlib import Path

from cha import colors, config


def fzf_directory_navigation(target_dir=None):
    """
    fzf-based directory navigation system.
    if target_dir is provided, navigate there directly if it exists.
    otherwise, start from $HOME and allow user to navigate through directories.
    """
    if target_dir and os.path.isdir(target_dir):
        return os.path.abspath(target_dir)

    # start from home directory
    current_dir = os.path.expanduser("~")
    dir_history = []

    try:
        while True:
            # get directories in current directory
            try:
                entries = []
                for entry in os.listdir(current_dir):
                    entry_path = os.path.join(current_dir, entry)
                    if os.path.isdir(entry_path):
                        entries.append(entry)

                # sort directories
                entries.sort()

                # if no subdirectories, go directly to final selection
                if not entries:
                    # add current directory to history if not already present
                    if current_dir not in dir_history:
                        dir_history.append(current_dir)
                    break

                # add exit option at the bottom
                entries_with_exit = entries + [config.EXIT_SELECTION_TAG]

                # run fzf to select directory
                from cha import utils

                selected_dir = utils.run_fzf_ssh_safe(
                    [
                        "fzf",
                        "--reverse",
                        "--height=40%",
                        "--border",
                        "--prompt=select directory: ",
                        "--header",
                        f"current: {current_dir}",
                    ],
                    "\n".join(entries_with_exit),
                )
                if not selected_dir or selected_dir == config.EXIT_SELECTION_TAG:
                    break

                # navigate to selected directory
                new_dir = os.path.join(current_dir, selected_dir)
                if os.path.isdir(new_dir):
                    current_dir = new_dir
                    # add directory to history if not already present
                    if current_dir not in dir_history:
                        dir_history.append(current_dir)
                else:
                    print(colors.red(f"directory not found: {selected_dir}"))
                    break

            except subprocess.CalledProcessError:
                # user cancelled (esc, ctrl-c, ctrl-d) - exit immediately
                return None
            except Exception as e:
                print(colors.red(f"error: {e}"))
                break

    except KeyboardInterrupt:
        # user cancelled with ctrl-c - exit immediately
        return None

    # if we have history, let user pick final destination
    if dir_history:
        return select_final_directory(dir_history)

    # return None to indicate no directory was selected
    return None


def select_final_directory(dir_history):
    """
    show all directories user visited and let them pick the final one
    """
    try:
        # format directories for display
        formatted_dirs = []
        for i, dir_path in enumerate(dir_history):
            formatted_dirs.append(f"{i+1}. {dir_path}")
        # add exit option at the bottom
        formatted_dirs.append(config.EXIT_SELECTION_TAG)

        from cha import utils

        selected_line = utils.run_fzf_ssh_safe(
            [
                "fzf",
                "--reverse",
                "--height=40%",
                "--border",
                "--prompt=select final directory: ",
                "--header",
                "choose where to move cha",
            ],
            "\n".join(formatted_dirs),
        )
        if selected_line and selected_line != config.EXIT_SELECTION_TAG:
            # extract directory path from formatted line
            selected_dir = selected_line.split(". ", 1)[1]
            return selected_dir

    except subprocess.CalledProcessError:
        # user cancelled - return None
        return None
    except Exception as e:
        print(colors.red(f"error selecting final directory: {e}"))

    # return None to indicate no directory was selected
    return None
