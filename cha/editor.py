import subprocess
import readline
import tempfile
import difflib
import os

from cha import colors, utils, loading, config


def is_fzf_available():
    try:
        subprocess.run(["fzf", "--version"], capture_output=True, check=True)
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        return False


FZF_AVAILABLE = is_fzf_available()


class InteractiveEditor:

    def __init__(self, client, model_name, file_path=None):
        self.client = client
        self.model_name = model_name
        self.file_path = file_path
        self.original_content = ""
        self.current_content = ""
        self.undo_stack = []
        self.history_file = os.path.join(tempfile.gettempdir(), ".cha_editor_history")

    def run(self):
        try:
            if not self.file_path:
                self.file_path = self._select_file()

            if not self.file_path:
                print(colors.yellow("No file selected"))
                return

            self._load_file()
            if self.file_path is None:
                return

            self._setup_readline()

            print(colors.cyan(f"Editing: {self.file_path}"))
            print(
                colors.yellow("Type an edit request or 'help' for a list of commands.")
            )

            while True:
                try:
                    user_input = input(colors.blue(">>> ")).strip()
                    if not user_input:
                        continue
                    if not self._process_command(user_input):
                        break
                except (KeyboardInterrupt, EOFError):
                    print()
                    self._quit()
                    break
        finally:
            self._save_readline_history()

    def _select_file(self):
        if FZF_AVAILABLE:
            return self._select_file_with_fzf()
        else:
            try:
                file_path = input("enter file path to edit: ").strip()
                return os.path.abspath(file_path) if file_path else None
            except (KeyboardInterrupt, EOFError):
                return None

    def _select_file_with_fzf(self):
        try:
            current_dir = os.getcwd()
            all_files = []
            for root, dirs, files in os.walk(current_dir):
                dirs[:] = [
                    d
                    for d in dirs
                    if not d.startswith(".") and d not in config.DIRS_TO_IGNORE
                ]
                for file in files:
                    if not file.startswith(".") and not any(
                        file.endswith(ext) for ext in config.BINARY_EXTENSIONS
                    ):
                        all_files.append(
                            os.path.relpath(os.path.join(root, file), current_dir)
                        )

            all_files.sort(
                key=lambda f: os.path.getmtime(f) if os.path.exists(f) else 0,
                reverse=True,
            )

            from cha import utils

            fzf_process = utils.run_fzf_ssh_safe(
                [
                    "fzf",
                    "--reverse",
                    "--height=60%",
                    "--border",
                    "--prompt=select file or type to create: ",
                    "--preview",
                    "bat --style=numbers --color=always {} 2>/dev/null || head -n 50 {}",
                    "--print-query",
                ],
                "\n".join(all_files),
                return_process=True,
            )

            if fzf_process.returncode == 130:
                return None
            if fzf_process.returncode not in [0, 1]:
                return None

            output = fzf_process.stdout.strip().split("\n")

            if not output or not output[0]:
                return None

            selected = output[-1] if len(output) > 1 else output[0]

            return os.path.abspath(selected) if selected else None

        except (subprocess.SubprocessError, FileNotFoundError):
            return None

    def _load_file(self):
        if os.path.isdir(self.file_path):
            print(colors.red(f"Path {self.file_path} is a directory"))
            self.file_path = None
            return

        if not os.path.exists(self.file_path):
            try:
                os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
                with open(self.file_path, "w", encoding="utf-8") as f:
                    f.write("")
                print(colors.green(f"Created: {self.file_path}"))
            except IOError as e:
                print(colors.red(f"Failed to create file {e}"))
                self.file_path = None
                return

        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                self.original_content = f.read()
            self.current_content = self.original_content
        except (IOError, UnicodeDecodeError) as e:
            print(colors.red(f"Failed to read file: {e}"))
            self.file_path = None

    def _setup_readline(self):
        if os.path.exists(self.history_file):
            readline.read_history_file(self.history_file)
        readline.set_auto_history(True)

    def _save_readline_history(self):
        readline.write_history_file(self.history_file)

    def _show_help(self):
        help_options = [
            f"{config.HELP_ALL_ALIAS} = Show all help options",
            "h, help - Show this help message",
            "d, diff - Show differences between original and modified file",
            "s, save - Save the changes to the file",
            "u, undo - Undo the last change",
            "v, view - View the current file content in your default editor",
            "q, quit, exit - Exit the editor",
            f"{config.PICK_AND_RUN_A_SHELL_OPTION} - Run a shell command",
            f"{config.TEXT_EDITOR_INPUT_MODE} - Open editor for a long prompt",
        ]

        if FZF_AVAILABLE:
            try:
                from cha import utils

                selected_output = utils.run_fzf_ssh_safe(
                    [
                        "fzf",
                        "--reverse",
                        "--height=40%",
                        "--border",
                        "--prompt=Select a command to see details, ENTER to confirm, & Esc to cancel: ",
                        "--header",
                        f"Editing: {os.path.basename(self.file_path)}",
                    ],
                    "\n".join(help_options),
                )
                if selected_output:
                    selected_item = selected_output.strip()
                    if config.HELP_ALL_ALIAS in selected_item:
                        print(colors.yellow(f"Editing: {self.file_path}"))
                        for help_item in help_options:
                            if config.HELP_ALL_ALIAS not in help_item:
                                print(colors.yellow(help_item))
                    else:
                        print(colors.yellow(selected_item))
            except (subprocess.CalledProcessError, subprocess.SubprocessError):
                pass
        else:
            print(colors.yellow("Available commands:"))
            for option in help_options:
                if config.HELP_ALL_ALIAS not in option:
                    print(colors.yellow(f"  {option}"))

    def _process_command(self, user_input):
        command = user_input.lower()

        command_map = {
            "s": self._save_changes,
            "save": self._save_changes,
            "d": self._show_diff,
            "diff": self._show_diff,
            "u": self._undo_change,
            "undo": self._undo_change,
            "v": self._view_content,
            "view": self._view_content,
            "q": self._quit,
            "quit": self._quit,
            "exit": self._quit,
            "h": self._show_help,
            "help": self._show_help,
        }

        action = command_map.get(command)
        if action:
            action()
            if command in ["q", "quit", "exit"]:
                return False
        elif command.startswith(config.PICK_AND_RUN_A_SHELL_OPTION):
            shell_command = user_input[
                len(config.PICK_AND_RUN_A_SHELL_OPTION) :
            ].strip()
            utils.run_a_shell(shell_command if shell_command else None)
        elif command == config.TEXT_EDITOR_INPUT_MODE:
            editor_content = utils.check_terminal_editors_and_edit()
            if editor_content:
                self._make_edit_request(editor_content)
            else:
                print(colors.yellow("No input received from editor."))
        else:
            self._make_edit_request(user_input)
        return True

    def _make_edit_request(self, request):
        loading.start_loading("processing request")
        try:
            messages = [
                {"role": "system", "content": config.EDITOR_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": f"file path: {self.file_path}\n\noriginal content:\n```\n{self.current_content}\n```\n\nedit request: {request}",
                },
            ]
            response = self.client.chat.completions.create(
                model=self.model_name, messages=messages, temperature=0.1
            )
            new_content = response.choices[0].message.content

            if new_content.startswith("```") and new_content.endswith("```"):
                new_content = "\n".join(new_content.split("\n")[1:-1])

            loading.stop_loading()

            if self.current_content != new_content:
                self.undo_stack.append(self.current_content)
                self.current_content = new_content
                self._show_diff()
            else:
                print(colors.yellow("No changes were generated"))

        except Exception as e:
            loading.stop_loading()
            print(colors.red(f"{e}"))

    def _show_diff(self):
        if self.original_content == self.current_content:
            print(colors.yellow("No changes to show"))
            return

        diff = difflib.unified_diff(
            self.original_content.splitlines(keepends=True),
            self.current_content.splitlines(keepends=True),
            fromfile=f"original: {self.file_path}",
            tofile=f"modified: {self.file_path}",
            lineterm="",
        )

        has_diff = False
        for line in diff:
            has_diff = True
            if line.startswith("+") and not line.startswith("+++"):
                print(colors.green(line), end="")
            elif line.startswith("-") and not line.startswith("---"):
                print(colors.red(line), end="")
            elif line.startswith("@@"):
                print(colors.yellow(line), end="")
            else:
                print(line, end="")

        if not has_diff:
            print(colors.yellow("No changes to show"))
        print()

    def _save_changes(self):
        if self.original_content == self.current_content:
            print(colors.yellow("No changes to save"))
            return
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                f.write(self.current_content)
            self.original_content = self.current_content
            self.undo_stack.clear()
            print(colors.green(f"Saved: {self.file_path}"))
        except IOError as e:
            print(colors.red(f"Error saving file: {e}"))

    def _undo_change(self):
        if not self.undo_stack:
            print(colors.yellow("No changes to undo"))
            return
        self.current_content = self.undo_stack.pop()
        print(colors.green("Last change undone"))
        self._show_diff()

    def _view_content(self):
        if self.original_content != self.current_content:
            try:
                prompt = colors.red("Save before viewing (y/N)? ")
                save_changes = input(prompt).lower()
                if save_changes == "y":
                    self._save_changes()
            except (KeyboardInterrupt, EOFError):
                print()
                return

        if not utils.open_file_in_editor(self.file_path):
            print(colors.red("Failed to open a terminal editor"))
            return

        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                new_content = f.read()
            if new_content != self.current_content:
                self.current_content = new_content
                print(colors.yellow("Reloaded file from disk"))
                self._show_diff()
        except (IOError, UnicodeDecodeError) as e:
            print(colors.red(f"Failed to reload file: {e}"))

    def _quit(self):
        if self.original_content != self.current_content:
            try:
                prompt = colors.red("Save before quitting (y/N)? ")
                save_changes = input(prompt).lower()
                if save_changes == "y":
                    self._save_changes()
            except (KeyboardInterrupt, EOFError):
                print()
                pass


def run_editor(client, model_name, file_path=None):
    editor = InteractiveEditor(client, model_name, file_path=file_path)
    editor.run()


def call_editor(client, initial_prompt, model_name):
    editor = InteractiveEditor(client, model_name, file_path=initial_prompt)
    editor.run()
