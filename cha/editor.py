import difflib
import subprocess
import tempfile
import os
import sys
import readline

from cha import colors, utils, loading, config

# attempt to import pygments for syntax highlighting
try:
    from pygments import highlight
    from pygments.lexers import get_lexer_by_name, guess_lexer_for_filename
    from pygments.formatters import TerminalFormatter

    PYGMENTS_AVAILABLE = True
except ImportError:
    PYGMENTS_AVAILABLE = False


# check if fzf is available
def is_fzf_available():
    """check if fzf is installed and in the path."""
    try:
        subprocess.run(["fzf", "--version"], capture_output=True, check=True)
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        return False


FZF_AVAILABLE = is_fzf_available()


class InteractiveEditor:
    """a class to handle interactive file editing sessions."""

    def __init__(self, client, model_name, file_path=None):
        self.client = client
        self.model_name = model_name
        self.file_path = file_path
        self.original_content = ""
        self.current_content = ""
        self.undo_stack = []
        self.history_file = os.path.join(tempfile.gettempdir(), ".cha_editor_history")

    def run(self):
        """start the interactive editing session."""
        try:
            if not self.file_path:
                self.file_path = self._select_file()

            if not self.file_path:
                print(colors.yellow("no file selected, exiting"))
                return

            self._load_file()
            # loading failed
            if self.file_path is None:
                return

            self._setup_readline()

            print(colors.cyan(f"editing: {self.file_path}"))
            print(
                colors.yellow(
                    "type your edit request or a command: diff, save, undo, view, quit"
                )
            )

            while True:
                try:
                    user_input = input(colors.blue(">>> ")).strip()
                    if not user_input:
                        continue
                    # exit loop if process_command returns false
                    if not self._process_command(user_input):
                        break
                except (KeyboardInterrupt, EOFError):
                    print()
                    self._quit()
                    break
        finally:
            self._save_readline_history()

    def _select_file(self):
        """select a file, using fzf if available."""
        if FZF_AVAILABLE:
            return self._select_file_with_fzf()
        else:
            try:
                file_path = input("enter file path to edit: ").strip()
                return os.path.abspath(file_path) if file_path else None
            except (KeyboardInterrupt, EOFError):
                return None

    def _select_file_with_fzf(self):
        """select a file using fzf with smart options."""
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

            fzf_process = subprocess.run(
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
                input="\n".join(all_files).encode(),
                capture_output=True,
            )

            # handle different exit codes
            # 130: user aborted (esc, ctrl-c)
            if fzf_process.returncode == 130:
                return None
            # 0: match found, 1: no match (but user entered text)
            if fzf_process.returncode not in [0, 1]:
                # other errors
                return None

            output = fzf_process.stdout.decode().strip().split("\n")

            if not output or not output[0]:
                return None

            # if user selected an item, it's the last line, otherwise it's the query
            selected = output[-1] if len(output) > 1 else output[0]

            return os.path.abspath(selected) if selected else None

        except (subprocess.SubprocessError, FileNotFoundError):
            return None

    def _load_file(self):
        """load file content or create a new file."""
        if os.path.isdir(self.file_path):
            print(colors.red(f"error: {self.file_path} is a directory"))
            self.file_path = None
            return

        if not os.path.exists(self.file_path):
            try:
                os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
                with open(self.file_path, "w", encoding="utf-8") as f:
                    f.write("")
                print(colors.green(f"created: {self.file_path}"))
            except IOError as e:
                print(colors.red(f"failed to create file: {e}"))
                self.file_path = None
                return

        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                self.original_content = f.read()
            self.current_content = self.original_content
        except (IOError, UnicodeDecodeError) as e:
            print(colors.red(f"failed to read file: {e}"))
            self.file_path = None

    def _setup_readline(self):
        """set up readline for persistent history."""
        if os.path.exists(self.history_file):
            readline.read_history_file(self.history_file)
        readline.set_auto_history(True)

    def _save_readline_history(self):
        """save readline history to a file."""
        readline.write_history_file(self.history_file)

    def _process_command(self, user_input):
        """process user input, routing to commands or edit requests."""
        command = user_input.lower()

        command_map = {
            "save": self._save_changes,
            "diff": self._show_diff,
            "undo": self._undo_change,
            "view": self._view_content,
            "quit": self._quit,
            "exit": self._quit,
        }

        action = command_map.get(command)
        if action:
            action()
            if command in ["quit", "exit"]:
                # signal to exit loop
                return False
        else:
            self._make_edit_request(user_input)
        # signal to continue loop
        return True

    def _make_edit_request(self, request):
        """send edit request to the ai and update content."""
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

            # clean the response: remove backticks and language identifiers
            if new_content.startswith("```") and new_content.endswith("```"):
                new_content = "\n".join(new_content.split("\n")[1:-1])

            loading.stop_loading()

            if self.current_content != new_content:
                self.undo_stack.append(self.current_content)
                self.current_content = new_content
                self._show_diff()
            else:
                print(colors.yellow("no changes were generated"))

        except Exception as e:
            loading.stop_loading()
            print(colors.red(f"an error occurred: {e}"))

    def _show_diff(self):
        """show the diff between original and current content."""
        if self.original_content == self.current_content:
            print(colors.yellow("no changes to show"))
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
            print(colors.yellow("no changes to show"))
        print()

    def _save_changes(self):
        """save the current content to the file."""
        if self.original_content == self.current_content:
            print(colors.yellow("no changes to save"))
            return
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                f.write(self.current_content)
            self.original_content = self.current_content
            self.undo_stack.clear()
            print(colors.green(f"file saved: {self.file_path}"))
        except IOError as e:
            print(colors.red(f"error saving file: {e}"))

    def _undo_change(self):
        """revert the last change."""
        if not self.undo_stack:
            print(colors.yellow("no changes to undo"))
            return
        self.current_content = self.undo_stack.pop()
        print(colors.green("last change undone"))
        self._show_diff()

    def _view_content(self):
        """opens the file in a text editor and reloads it after changes."""
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
            print(colors.red("could not open any terminal editor"))
            return

        # after editor is closed, reload the file to get any external changes
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                new_content = f.read()
            if new_content != self.current_content:
                self.current_content = new_content
                print(colors.yellow("reloaded file from disk"))
                self._show_diff()
        except (IOError, UnicodeDecodeError) as e:
            print(colors.red(f"failed to reload file: {e}"))

    def _quit(self):
        """exit the editor, prompting to save if there are changes."""
        if self.original_content != self.current_content:
            try:
                prompt = colors.red("Save before quitting (y/N)? ")
                save_changes = input(prompt).lower()
                if save_changes == "y":
                    self._save_changes()
            except (KeyboardInterrupt, EOFError):
                # if user cancels prompt, just exit without saving
                print()
                pass


def call_editor(client, initial_prompt, model_name):
    """entry point for editor functionality."""
    editor = InteractiveEditor(client, model_name, file_path=initial_prompt)
    editor.run()
