import pkg_resources
import subprocess
import threading
import tempfile
import pathlib
import uuid
import sys
import os

from cha import utils, colors, loading
from openai import OpenAI


def run(code):
    # clean the code
    code = "\n".join(
        ln for ln in code.splitlines() if not ln.lstrip().startswith("```")
    ).strip()

    was_streamed = False

    # create temporary file
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", dir="/tmp", delete=False
    ) as tf:
        tf.write(code)
        script = pathlib.Path(tf.name)

    # run the code
    try:
        if "input(" in code:
            was_streamed = True
            # interactive mode with real-time output
            proc = subprocess.Popen(
                [sys.executable, str(script)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                # line-buffered
                bufsize=1,
            )

            out_lines, err_lines = [], []

            def read_pipe(pipe, lines_list, color_func):
                for char in iter(lambda: pipe.read(1), ""):
                    print(color_func(char), end="", flush=True)
                    lines_list.append(char)
                pipe.close()

            out_thread = threading.Thread(
                target=read_pipe, args=(proc.stdout, out_lines, colors.white)
            )

            err_thread = threading.Thread(
                target=read_pipe, args=(proc.stderr, err_lines, colors.red)
            )

            out_thread.start()
            err_thread.start()
            proc.wait(timeout=300)
            out_thread.join()
            err_thread.join()

            out, err = "".join(out_lines).strip(), "".join(err_lines).strip()
        else:
            # non-interactive mode
            proc = subprocess.run(
                [sys.executable, str(script)],
                capture_output=True,
                text=True,
                timeout=300,
            )
            out, err = proc.stdout.strip(), proc.stderr.strip()
    finally:
        script.unlink()

    return out, err, code, was_streamed


def coder(
    client: OpenAI,
    model: str,
    max_retries: int,
    prompt_code: str,
    prompt_answer: str,
    initial_prompt: str = None,
):
    try:
        if initial_prompt is None:
            q = input(colors.blue("Prompt: ")).strip()
            if not q:
                return []
        else:
            q = initial_prompt

        # initialize conversation history
        history = [
            {"role": "system", "content": prompt_code},
            {"role": "user", "content": q},
        ]

        retries = 0
        prev_code = prev_issue = ""

        while retries < max_retries + 1:
            loading.start_loading("Generating code")
            if prev_err := prev_issue:
                user_msg = f"Here was the previous script that failed or produced no output:\n{prev_code}\nError or issue:\n{prev_err}\nPlease return a FIXED version."
                history.append({"role": "user", "content": user_msg})

            buf = ""
            try:
                for ch in client.chat.completions.create(
                    model=model, messages=history, stream=True
                ):
                    # stop loading before first character is printed
                    if buf == "":
                        loading.stop_loading()
                    part = ch.choices[0].delta.content or ""
                    buf += part
                    print(colors.green(part), end="", flush=True)
                # add newline after code
                print()
            except Exception as e:
                # ensure loading is stopped even if streaming fails
                loading.stop_loading()
                raise e

            raw = buf.strip()
            history.append({"role": "assistant", "content": raw})

            # ask for confirmation to run
            action = input(colors.blue("Run (Y/n) or modify? ")).strip()
            action_lower = action.lower()

            # check for yes/no responses
            if not action or action_lower.startswith("y"):
                pass
            elif len(action) > 5:
                # treat as modification prompt
                history.append({"role": "user", "content": action})
                prev_issue = ""
                continue
            elif action_lower.startswith("n"):
                return history
            else:
                print(
                    colors.red(
                        "Invalid input. Please enter 'y', 'n', or a modification prompt (>5 characters)."
                    )
                )
                continue

            # run the code
            stdout, stderr, code, was_streamed = run(raw)
            if not was_streamed:
                if stdout:
                    formatted_output = "\n".join(
                        f'{colors.blue("> ")}{line}' for line in stdout.splitlines()
                    )
                    loading.print_message(formatted_output)
                if stderr:
                    print(colors.red(stderr), end="")

            success = bool(stdout) and not stderr

            if success:
                # add execution result to history
                history.append(
                    {"role": "user", "content": f"Execution output:\n{stdout}"}
                )

                # stream the final answer using full history but with answer prompt
                loading.start_loading("Generating answer")
                answer_history = [
                    {"role": "system", "content": prompt_answer}
                ] + history[-1:]

                buf = ""
                try:
                    for ch in client.chat.completions.create(
                        model=model,
                        messages=answer_history,
                        stream=True,
                    ):
                        if buf == "":
                            loading.stop_loading()
                        part = ch.choices[0].delta.content or ""
                        buf += part
                        print(colors.green(part), end="", flush=True)
                except Exception as e:
                    loading.stop_loading()
                    raise e

                # add final answer to history
                history.append({"role": "assistant", "content": buf.strip()})
                if not buf.strip().endswith("\n"):
                    print()
                return history

            # handle failure
            issue = stderr or "[no output produced]"
            print(colors.red("Issue detected:"))
            print(colors.red(issue))
            retries += 1
            if retries > max_retries:
                print(colors.red("Reached maximum retries - exiting."))
                return history
            prev_code, prev_issue = code, issue
            if (
                not input(colors.blue("Attempt to auto-fix and rerun? [y/N]: "))
                .strip()
                .lower()
                .startswith("y")
            ):
                return history
    except (KeyboardInterrupt, EOFError):
        loading.stop_loading()
        print()
        raise


def call_coder(client, initial_prompt, model_name, max_retries):
    allowed_imports = []
    installed_packages = pkg_resources.working_set
    package_list = sorted([f"{i.key}=={i.version}" for i in installed_packages])
    for package in package_list:
        allowed_imports.append(package)

    system_prompt_code = utils.rls(
        f"""
        You are an advanced Python coding assistant.

        ✱ OBJECTIVE
        Return a single, self-contained Python 3 script that fulfils the user's request.

        ✱ ALLOWED IMPORTS
        {", ".join(allowed_imports)}

        ✱ MANDATORY FORMAT & BEHAVIOR  
        1. Raw code only  **no** markdown back-ticks, comments, or extra text.  
        2. First non-blank character must be Python code.  
        3. The script **must call `print()`** (or an equivalent) so its final answer appears on stdout.  
        4. No blank lines before the first or after the last line of code.
        5. DO NOT use any interactive input (no input() functions). Instead, hardcode example values or use command line arguments if needed.
        """
    )

    answer_prompt = "Using ONLY the execution output provided, answer the user's original question plainly and MAKE SURE NOT to end your answer with a period unless it makes sense to do so"

    conversation_history = coder(
        client=client,
        initial_prompt=initial_prompt,
        model=model_name,
        max_retries=max_retries,
        prompt_code=system_prompt_code,
        prompt_answer=answer_prompt,
    )

    try:
        save_response = input(colors.blue("Save the code (Y/n)? ")).lower().strip()

        if save_response in ["y", "yes"]:
            filename_response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {
                        "role": "user",
                        "content": "Based on the code above, suggest a simple and descriptive filename (just the filename, no explanation). Include appropriate file extension which most of the time is python; <filename>.py",
                    },
                    conversation_history[-3],
                ],
                max_tokens=10,
            )

            suggested_filename = (
                filename_response.choices[0]
                .message.content.strip()
                .lower()
                .replace(" ", "_")
            )

            if not suggested_filename.endswith(".py"):
                suggested_filename = suggested_filename.split(".")[0] + ".py"

            suggested_filename = "export_" + suggested_filename

            final_filename = suggested_filename
            if os.path.exists(final_filename):
                final_filename = f"{os.path.splitext(suggested_filename)[0]}_{str(uuid.uuid4())[:8]}{os.path.splitext(suggested_filename)[1]}"

            with open(os.path.join(os.getcwd(), final_filename), "w") as f:
                f.write(conversation_history[-3]["content"])

            print(colors.green(f"Saved code to {final_filename}"))
    except (KeyboardInterrupt, EOFError):
        print()
        pass

    return conversation_history
