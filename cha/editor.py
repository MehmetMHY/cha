import subprocess
import readline
import tempfile
import difflib
import select
import pty
import sys
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
    class ChaAbortException(Exception):
        # custom exception to force exit from Cha entirely
        pass

    def __init__(self, client, model_name, file_path=None, chat_history=None):
        self.client = client
        self.model_name = model_name
        self.file_path = file_path
        self.chat_history = chat_history or []
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

            file_was_created = self._load_file()
            if self.file_path is None:
                return

            self._setup_readline()

            if not file_was_created:
                print(colors.cyan(f"Editing: {self.file_path}"))
            print(
                colors.yellow("Type an edit request or 'help' for a list of commands")
            )

            while True:
                try:
                    prompt = f"\001{config.TERMINAL_THEME_CODES['colors']['blue']}\002>>> \001{config.TERMINAL_THEME_CODES['reset']}\002"
                    user_input = input(prompt).strip()
                    if not user_input:
                        continue
                    if not self._process_command(user_input):
                        break
                except (KeyboardInterrupt, EOFError):
                    loading.stop_loading()
                    print()
                    break
                except SystemExit:
                    break
                except InteractiveEditor.ChaAbortException:
                    # Re-raise the abort exception to let it propagate to main.py
                    raise
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
        file_was_created = False

        if os.path.isdir(self.file_path):
            print(colors.red(f"Path {self.file_path} is a directory"))
            self.file_path = None
            return False

        if not os.path.exists(self.file_path):
            try:
                os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
                with open(self.file_path, "w", encoding="utf-8") as f:
                    f.write("")
                print(colors.green(f"Created: {self.file_path}"))
                file_was_created = True
            except IOError as e:
                print(colors.red(f"Failed to create file {e}"))
                self.file_path = None
                return False

        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                self.original_content = f.read()
            self.current_content = self.original_content
        except (IOError, UnicodeDecodeError) as e:
            print(colors.red(f"Failed to read file: {e}"))
            self.file_path = None
            return False

        return file_was_created

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
            "r, run - Execute the current file with LLM-generated command",
            "q, quit, exit - Exit the editor",
            "Q, abort - Exit the entire Cha instance",
            f"{config.PICK_AND_RUN_A_SHELL_OPTION} - Run a shell command",
            f"{config.TEXT_EDITOR_INPUT_MODE} - Open editor for a long prompt",
            f"{config.USE_CODE_DUMP} - Codedump a directory as context",
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
                        if "abort" in selected_item:
                            command_alias = "Q"  # Use Q to trigger complete exit
                        else:
                            command_alias = selected_item.split(",")[0].split(" ")[0]
                        if command_alias:
                            result = self._process_command(command_alias)
                            if not result:
                                return False  # Signal to exit editor
            except (subprocess.CalledProcessError, subprocess.SubprocessError):
                pass
        else:
            print(colors.yellow("Available commands:"))
            for option in help_options:
                if config.HELP_ALL_ALIAS not in option:
                    print(colors.yellow(f"  {option}"))

        return None  # Continue editor by default

    def _process_command(self, user_input):
        # Handle case-sensitive commands first
        if user_input == "Q":
            self._complete_exit()
            # The exception should be raised above, but if we get here something went wrong
            return False

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
            "r": self._run_script,
            "run": self._run_script,
            "q": self._quit,
            "quit": self._quit,
            "exit": self._quit,
            "abort": self._complete_exit,
            "h": self._show_help,
            "help": self._show_help,
            config.HELP_PRINT_OPTIONS_KEY: self._show_help,
        }

        action = command_map.get(command)
        if action:
            if command in ["h", "help", config.HELP_PRINT_OPTIONS_KEY]:
                result = action()
                if result is False:
                    return False
            else:
                action()
                if command in ["q", "quit", "exit"]:
                    return False
                elif command == "abort":
                    return False
        elif command.startswith(config.PICK_AND_RUN_A_SHELL_OPTION):
            shell_command = user_input[
                len(config.PICK_AND_RUN_A_SHELL_OPTION) :
            ].strip()
            utils.run_a_shell(shell_command if shell_command else None)
        elif command == config.TEXT_EDITOR_INPUT_MODE:
            editor_content = utils.check_terminal_editors_and_edit()
            if editor_content:
                for line in editor_content.rstrip("\n").split("\n"):
                    print(colors.blue(">"), line)
                self._make_edit_request(editor_content)
            else:
                print(colors.yellow("No input received from editor"))
        elif command.startswith(config.USE_CODE_DUMP):
            dir_path = user_input.replace(config.USE_CODE_DUMP, "").strip()
            if not dir_path or "/" not in dir_path:
                dir_path = None
            self._codedump_request(dir_path)
        elif user_input.strip().endswith(config.SKIP_SEND_TEXT):
            pass
        else:
            self._make_edit_request(user_input)
        return True

    def _make_edit_request(self, request):
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                self.current_content = f.read()
        except (IOError, UnicodeDecodeError) as e:
            print(colors.red(f"Failed to read file: {e}"))
            return

        loading.start_loading("processing request")
        try:
            # build context with execution history if available
            context_info = f"file path: {self.file_path}\n\noriginal content:\n```\n{self.current_content}\n```"

            if self.chat_history and len(self.chat_history) > 1:
                relevant_history = self.chat_history[1:]
                if relevant_history:
                    context_info += f"\n\nchat history context:\n"
                    for i, item in enumerate(relevant_history[-5:], 1):
                        if item.get("user"):
                            context_info += f"User {i}: {item['user'][:200]}{'...' if len(item['user']) > 200 else ''}\n"
                        if item.get("bot"):
                            context_info += f"Bot {i}: {item['bot'][:200]}{'...' if len(item['bot']) > 200 else ''}\n"

            if hasattr(self, "execution_history") and self.execution_history:
                context_info += f"\n\nrecent execution history:\n"
                for i, execution in enumerate(
                    self.execution_history[-3:], 1
                ):  # last 3 executions
                    context_info += (
                        f"{i}. {execution['timestamp']}: {execution['context']}\n"
                    )

            context_info += f"\n\nedit request: {request}"

            messages = [
                {"role": "system", "content": config.EDITOR_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": context_info,
                },
            ]
            api_params = {"model": self.model_name, "messages": messages}
            if not utils.is_slow_model(self.model_name):
                api_params["temperature"] = 0.1
            response = self.client.chat.completions.create(**api_params)
            new_content = response.choices[0].message.content
            loading.stop_loading()

            if new_content.startswith("```") and new_content.endswith("```"):
                new_content = "\n".join(new_content.split("\n")[1:-1])

            if self.current_content != new_content:
                self.undo_stack.append(self.current_content)
                self.current_content = new_content
                self._show_diff()
            else:
                print(colors.yellow("No changes were generated"))

        except (KeyboardInterrupt, EOFError):
            print()
        except Exception as e:
            print(colors.red(f"{e}"))
        finally:
            loading.stop_loading()

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

    def _run_script(self):
        if self.original_content != self.current_content:
            self._save_changes()

        loading.start_loading("Generating run command")
        try:
            # generate execution command using LLM
            messages = [
                {
                    "role": "system",
                    "content": "You are a script execution assistant. Given a file path and its content, generate the appropriate command to execute it. Consider the file extension, shebang lines, and content to determine the best execution method. Return ONLY the command without any explanation or markdown formatting.",
                },
                {
                    "role": "user",
                    "content": f"File path: {self.file_path}\n\nFile content:\n```\n{self.current_content}\n```\n\nGenerate the command to execute this file:",
                },
            ]

            api_params = {
                "model": self.model_name,
                "messages": messages,
                "max_tokens": 100,
            }
            if not utils.is_slow_model(self.model_name):
                api_params["temperature"] = 0.1

            response = self.client.chat.completions.create(**api_params)

            generated_command = response.choices[0].message.content.strip()
            loading.stop_loading()

            print(colors.cyan(generated_command))

            # ask for confirmation or allow editing
            action = ""
            try:
                action = (
                    input(colors.blue("Execute (Y), edit (e), or cancel (n)? "))
                    .strip()
                    .lower()
                )
            except (KeyboardInterrupt, EOFError):
                print(colors.yellow("\nExecution cancelled"))
                return

            if action == "e":
                # allow user to edit the command using text editor
                import tempfile

                with tempfile.NamedTemporaryFile(
                    mode="w+", suffix=".sh", delete=False
                ) as tmp_file:
                    tmp_file.write(generated_command)
                    tmp_file_path = tmp_file.name

                if utils.open_file_in_editor(tmp_file_path):
                    try:
                        with open(tmp_file_path, "r") as f:
                            edited_command = f.read().strip()
                        os.unlink(tmp_file_path)
                        if edited_command:
                            generated_command = edited_command
                            print(colors.cyan(f"Updated command: {generated_command}"))
                        else:
                            print(
                                colors.yellow(
                                    "No command provided, cancelling execution"
                                )
                            )
                            return
                    except (IOError, UnicodeDecodeError) as e:
                        print(colors.red(f"Failed to read edited command: {e}"))
                        os.unlink(tmp_file_path)
                        return
                else:
                    print(colors.red("Failed to open text editor"))
                    os.unlink(tmp_file_path)
                    return

                # ask for final confirmation after editing
                try:
                    final_action = (
                        input(colors.blue("Execute edited command (Y/n)? "))
                        .strip()
                        .lower()
                    )
                    if final_action and final_action != "y":
                        print(colors.yellow("Execution cancelled"))
                        return
                except (KeyboardInterrupt, EOFError):
                    print(colors.yellow("\nExecution cancelled"))
                    return

            elif action and action != "y":
                print(colors.yellow("Execution cancelled"))
                return

            # execute the command
            print(colors.green("Executing..."))
            process = None
            master_fd = None
            try:
                master_fd, slave_fd = pty.openpty()

                process = subprocess.Popen(
                    generated_command,
                    shell=True,
                    stdin=slave_fd,
                    stdout=slave_fd,
                    stderr=slave_fd,
                    cwd=os.path.dirname(self.file_path),
                    preexec_fn=os.setsid,
                )
                os.close(slave_fd)

                output_lines = []
                while process.poll() is None:
                    try:
                        r, _, _ = select.select([master_fd], [], [], 0.1)
                        if r:
                            output = os.read(master_fd, 1024).decode()
                            if output:
                                sys.stdout.write(output)
                                sys.stdout.flush()
                                output_lines.append(output)
                            else:  # EOF
                                break
                    except OSError:
                        break  # EIO error means slave PTY has been closed

                retcode = process.wait()
                output = "".join(output_lines)

                if retcode != 0:
                    print(colors.red(f"Command exited with code {retcode}"))
                    error_context = f"Execution failed with command: {generated_command}\nReturn code: {retcode}\nOutput:\n{output}"
                    print(
                        colors.yellow(
                            "Execution context added for debugging assistance"
                        )
                    )
                    self._add_execution_context(error_context)
                else:
                    success_context = (
                        f"Successfully executed: {generated_command}\nOutput:\n{output}"
                    )
                    self._add_execution_context(success_context)

            except KeyboardInterrupt:
                if process and process.poll() is None:
                    os.killpg(
                        os.getpgid(process.pid), 9
                    )  # Kill the whole process group
                    process.wait()
                    print(colors.red("Process terminated"))
            except Exception as e:
                print(colors.red(f"Execution failed: {e}"))
            finally:
                if master_fd:
                    os.close(master_fd)

        except (KeyboardInterrupt, EOFError):
            print(colors.yellow("\nCommand generation cancelled"))
        except Exception as e:
            print(colors.red(f"Failed to generate run command: {e}"))
        finally:
            loading.stop_loading()

    def _codedump_request(self, dir_path=None):
        try:
            from cha import codedump

            loading.start_loading("Generating codedump")

            report = codedump.code_dump(
                dir_full_path=dir_path, output_to_stdout=True, auto_include_all=False
            )

            if report:
                self._make_edit_request(f"Here's the codebase context:\n\n{report}")
            else:
                print(colors.yellow("No codedump content generated"))
        except (KeyboardInterrupt, EOFError):
            print(colors.yellow("\nCodedump cancelled"))
        except Exception as e:
            print(colors.red(f"Codedump failed: {e}"))
        finally:
            loading.stop_loading()

    def _add_execution_context(self, context):
        if not hasattr(self, "execution_history"):
            self.execution_history = []
        self.execution_history.append(
            {
                "timestamp": subprocess.run(
                    ["date"], capture_output=True, text=True
                ).stdout.strip(),
                "context": context,
            }
        )

    def _complete_exit(self):
        raise self.ChaAbortException("User requested complete exit from Cha")

    def _quit(self):
        if self.original_content != self.current_content:
            try:
                prompt = colors.red("Save before quitting (y/N)? ")
                save_changes = input(prompt).lower()
                if save_changes == "y":
                    self._save_changes()
            except (KeyboardInterrupt, EOFError):
                print(colors.yellow("\nQuitting without save..."))
                pass


def run_editor(client, model_name, file_path=None, chat_history=None):
    editor = InteractiveEditor(
        client, model_name, file_path=file_path, chat_history=chat_history
    )
    editor.run()
