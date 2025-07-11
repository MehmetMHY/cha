import difflib
import subprocess
import tempfile
import os
import sys

from cha import colors, utils, loading, traverse, config
from openai import OpenAI


def show_diff(original_content, new_content, file_path):
    if original_content == new_content:
        print(colors.yellow("no changes detected"))
        return False

    diff = difflib.unified_diff(
        original_content.splitlines(keepends=True),
        new_content.splitlines(keepends=True),
        fromfile=f"original/{os.path.basename(file_path)}",
        tofile=f"modified/{os.path.basename(file_path)}",
        lineterm="",
    )

    for line in diff:
        if line.startswith("+") and not line.startswith("+++"):
            print(colors.green(line), end="")
        elif line.startswith("-") and not line.startswith("---"):
            print(colors.red(line), end="")
        elif line.startswith("@@"):
            print(colors.yellow(line), end="")
        else:
            print(line, end="")
    print()

    return True


def run_editor(client: OpenAI, model_name: str, initial_prompt: str = None):
    try:
        if initial_prompt:
            file_path = initial_prompt.strip()
            if not os.path.isabs(file_path):
                file_path = os.path.abspath(file_path)
        else:
            file_path = traverse.msg_content_load(
                client, simple=True, return_path_only=True
            )

        if not file_path:
            print(colors.yellow("no file selected, opening shell"))
            utils.run_a_shell()
            return

        if os.path.isdir(file_path):
            print(colors.red("cannot edit directory"))
            return

        if not os.path.exists(file_path):
            print(colors.red(f"file does not exist: {file_path}"))
            return

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                original_content = f.read()
        except Exception as e:
            print(colors.red(f"failed to read file: {e}"))
            return

        while True:
            try:
                user_request = input(colors.blue(">>> ")).strip()

                if user_request.lower() == "q":
                    break
                elif user_request.lower() == "shell":
                    original_cwd = os.getcwd()
                    try:
                        os.chdir(os.path.dirname(file_path))
                        utils.run_a_shell()
                    finally:
                        os.chdir(original_cwd)
                    continue
                elif not user_request:
                    continue

                loading.start_loading("processing")

                messages = [
                    {
                        "role": "system",
                        "content": config.EDITOR_SYSTEM_PROMPT,
                    },
                    {
                        "role": "user",
                        "content": f"file path: {file_path}\n\noriginal content:\n{original_content}\n\nedit request: {user_request}",
                    },
                ]

                response = client.chat.completions.create(
                    model=model_name, messages=messages, temperature=0.1
                )

                loading.stop_loading()
                new_content = response.choices[0].message.content

                if show_diff(original_content, new_content, file_path):
                    action = (
                        input(colors.blue("(s)ave, (e)dit, (m)odify, (r)eject: "))
                        .strip()
                        .lower()
                    )

                    if action == "s":
                        with open(file_path, "w", encoding="utf-8") as f:
                            f.write(new_content)
                        original_content = new_content
                        print(colors.green("saved"))
                    elif action == "e":
                        with tempfile.NamedTemporaryFile(
                            mode="w", suffix=".tmp", delete=False
                        ) as temp_file:
                            temp_file.write(new_content)
                            temp_path = temp_file.name

                        try:
                            subprocess.run(
                                [config.PREFERRED_TERMINAL_IDE or "vi", temp_path]
                            )
                            with open(temp_path, "r") as f:
                                modified_content = f.read()

                            if show_diff(original_content, modified_content, file_path):
                                if (
                                    input(colors.blue("save? (y/n): ")).strip().lower()
                                    == "y"
                                ):
                                    with open(file_path, "w", encoding="utf-8") as f:
                                        f.write(modified_content)
                                    original_content = modified_content
                                    print(colors.green("saved"))
                        except Exception as e:
                            print(colors.red(f"editor failed: {e}"))
                        finally:
                            try:
                                os.unlink(temp_path)
                            except:
                                pass
                    elif action == "r":
                        print(colors.yellow("rejected"))

            except (KeyboardInterrupt, EOFError):
                print()
                break
            except Exception as e:
                loading.stop_loading()
                print(colors.red(f"error: {e}"))

    except (KeyboardInterrupt, EOFError):
        print()
        return


def call_editor(client, initial_prompt, model_name):
    return run_editor(client, model_name, initial_prompt)
