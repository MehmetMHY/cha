from collections import defaultdict
from pathlib import Path
import subprocess
import argparse
import fnmatch
import signal
import select
import time
import json
import sys
import os
import multiprocessing


def underline(text):
    return f"\u001b[4m{text}\u001b[0m"


def measure_startup_time(
    command="cha",
    prompt="User:",
    shell=None,
    timeout=10,
    poll_interval=0.01,
):
    start = time.perf_counter()
    shell = shell or os.environ.get("SHELL", "/bin/zsh")
    master, slave = os.openpty()
    proc = subprocess.Popen(
        [shell, "-l", "-c", command],
        stdin=slave,
        stdout=slave,
        stderr=slave,
        preexec_fn=os.setsid,
    )
    os.close(slave)
    data = ""
    try:
        while True:
            if time.perf_counter() - start > timeout:
                pgid = os.getpgid(proc.pid)
                os.killpg(pgid, signal.SIGTERM)
                raise TimeoutError(f"timeout({timeout}s)")
            ready, _, _ = select.select([master], [], [], poll_interval)
            if master in ready:
                chunk = os.read(master, 4096).decode(errors="ignore")
                if not chunk:
                    break
                data += chunk
                if prompt in data:
                    duration = time.perf_counter() - start
                    pgid = os.getpgid(proc.pid)
                    os.killpg(pgid, signal.SIGTERM)
                    return round(duration, 4)
    finally:
        if proc.poll() is None:
            try:
                pgid = os.getpgid(proc.pid)
                os.killpg(pgid, signal.SIGTERM)
            except Exception:
                pass
    return None


def over_all_startup_time(command_path, debug_mode=False, total_runs=15):
    times = []
    for i in range(total_runs):
        try:
            t = measure_startup_time(
                command=command_path, prompt="User:", shell="/bin/zsh"
            )
            if t is None:
                if debug_mode:
                    print("Prompt not detected")
            else:
                if debug_mode:
                    print(f"Startup time: {t:.4f} seconds")
                times.append(t)
        except TimeoutError as e:
            if debug_mode:
                print(e)
    if times:
        avg = sum(times) / len(times)
        print(f"{total_runs} total runs for '{os.path.basename(command_path)}'")
        print(f"Averaged {avg:.4f} seconds")
    else:
        print("No successful runs to average.")


def parse_gitignore(gitignore_path):
    patterns = []
    if os.path.exists(gitignore_path):
        with open(gitignore_path, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    patterns.append(line)
    return patterns


def is_ignored(file_path, ignore_patterns, base_dir):
    rel_path = os.path.relpath(file_path, base_dir).replace("\\", "/")

    for pattern in ignore_patterns:
        if pattern.endswith("/"):
            pattern = pattern.rstrip("/")
            if any(part == pattern for part in rel_path.split("/")):
                return True
        else:
            if fnmatch.fnmatch(rel_path, pattern) or fnmatch.fnmatch(
                os.path.basename(file_path), pattern
            ):
                return True
            if "/" not in pattern and fnmatch.fnmatch(
                os.path.basename(file_path), pattern
            ):
                return True
    return False


def count_lines_in_file(file_path):
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return sum(1 for _ in f)
    except:
        return 0


def count_lines_by_extension(
    directory, ext_targets=None, show_largest_file=False, show_file_count=False
):
    if not os.path.exists(directory):
        print(f"Directory '{directory}' does not exist.")
        return

    gitignore_path = os.path.join(directory, ".gitignore")
    ignore_patterns = parse_gitignore(gitignore_path)

    extension_data = defaultdict(
        lambda: {"count": 0, "max_file": "", "max_lines": 0, "file_count": 0}
    )
    total_size = 0
    total_files = 0
    processed_dirs = set()

    for root, dirs, files in os.walk(directory):
        dirs[:] = [
            d
            for d in dirs
            if not is_ignored(os.path.join(root, d), ignore_patterns, directory)
        ]

        for file in files:
            file_path = os.path.join(root, file)

            if is_ignored(file_path, ignore_patterns, directory):
                continue

            if os.path.isfile(file_path):
                total_files += 1
                processed_dirs.add(root)
                total_size += os.path.getsize(file_path)
                ext = Path(file).suffix or "no_extension"
                if ext_targets and ext not in ext_targets:
                    continue
                line_count = count_lines_in_file(file_path)
                extension_data[ext]["count"] += line_count
                extension_data[ext]["file_count"] += 1
                if line_count > extension_data[ext]["max_lines"]:
                    extension_data[ext]["max_lines"] = line_count
                    extension_data[ext]["max_file"] = os.path.relpath(
                        file_path, directory
                    )

    # print(f"Path: {directory}")
    total_num_dirs = len(processed_dirs)
    total_ext_types = len(extension_data)

    size_str = "0.00 KB"
    if total_size > 0:
        size_in_kb = total_size / 1024
        if size_in_kb > 1024:
            size_str = f"{size_in_kb / 1024:.2f} MB"
        else:
            size_str = f"{size_in_kb:.2f} KB"

    print(
        f"Files: {total_files} | Dirs: {total_num_dirs} | Exts: {total_ext_types} | Size: {size_str}"
    )

    if not extension_data:
        return

    fhd = "File Extension Stats:"
    if ext_targets == None:
        fhd = fhd.replace(":", " (ALL):")
    print(fhd)

    max_ext_len = max(
        len(".none" if "no_extension" in k else k) for k in extension_data.keys()
    )
    max_count_len = max(len(str(v["count"])) for v in extension_data.values())
    if show_largest_file:
        max_file_len = max(len(v["max_file"]) for v in extension_data.values())
        max_lines_len = max(len(str(v["max_lines"])) for v in extension_data.values())
    if show_file_count:
        max_file_count_len = max(
            len(str(v["file_count"])) for v in extension_data.values()
        )

    for ext, data in sorted(
        extension_data.items(), key=lambda item: item[1]["count"], reverse=True
    ):
        count = data["count"]
        if "no_extension" in ext:
            ext = ".none"

        output = f"{ext:<{max_ext_len}} = {str(count):>{max_count_len}} lines"
        if show_file_count:
            file_count = data["file_count"]
            output += f" | {str(file_count):>{max_file_count_len}} files"
        if show_largest_file:
            max_file = data["max_file"]
            max_lines = data["max_lines"]
            output += f" | {max_file:<{max_file_len}} = {str(max_lines):>{max_lines_len}} lines"
        print(output)


def depends_count(setup_file_path):
    lines = []
    with open(os.path.join(setup_file_path, "setup.py"), "r") as file:
        for line in file:
            lines.append(line.strip())

    packages = []
    for line in lines:
        if "==" in line:
            tmp = line.split("==")[0].strip().replace('"', "")
            packages.append(tmp)

    return packages


def analyze_git_repository(project_path):
    if not os.path.exists(project_path):
        print(f"Error: Path '{project_path}' does not exist")
        return

    if not os.path.isdir(os.path.join(project_path, ".git")):
        print(f"Error: '{project_path}' is not a git repository")
        return

    original_cwd = os.getcwd()
    try:
        os.chdir(project_path)

        def run_git_command(args):
            result = subprocess.run(
                ["git"] + args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            if result.returncode != 0:
                raise RuntimeError(
                    f"Git command failed: {' '.join(args)}\n{result.stderr.strip()}"
                )
            return result.stdout.strip()

        total_commits = int(run_git_command(["rev-list", "--count", "HEAD"]))

        output = run_git_command(["branch", "-a"])
        branches = [
            line.strip().lstrip("* ").strip()
            for line in output.split("\n")
            if line.strip()
        ]
        total_branches = len(branches)

        output = run_git_command(["log", "--format=%aN <%aE>"])
        contributors = set(output.split("\n"))
        total_contributors = len(contributors)

        output = run_git_command(["log", "--pretty=tformat:", "--numstat"])
        total_adds = 0
        total_deletes = 0
        for line in output.split("\n"):
            if line.strip() == "":
                continue
            parts = line.split("\t")
            if len(parts) < 3:
                continue
            adds, deletes, _ = parts
            if adds == "-":
                adds = 0
            if deletes == "-":
                deletes = 0
            adds = int(adds)
            deletes = int(deletes)
            total_adds += adds
            total_deletes += deletes
        total_edits = total_adds + total_deletes

        output = run_git_command(["log", "--merges", "--oneline"])
        total_merges = len(output.split("\n")) if output else 0

        output = run_git_command(["log", "--pretty=format:", "--name-only"])
        unique_files = set(line for line in output.split("\n") if line.strip())
        total_files_changed = len(unique_files)

        first_commit_date = run_git_command(["log", "--reverse", "--format=%ai", "-1"])
        latest_commit_date = run_git_command(["log", "--format=%ai", "-1"])

        print(f"First commit date:    {first_commit_date}")
        print(f"Latest commit date:   {latest_commit_date}")
        print(f"Total commits:         \u001b[94m{total_commits}\u001b[0m")
        print(f"Total contributors:   {total_contributors}")
        print(f"Total additions:       \u001b[92m{total_adds}\u001b[0m")
        print(f"Total deletions:       \u001b[91m{total_deletes}\u001b[0m")
        print(f"Total edits:           \u001b[93m{total_edits}\u001b[0m")
        print(f"Total files changed:  {total_files_changed}")
        print(f"Total branches:       {total_branches}")
        print(f"Total merge commits:  {total_merges}")

    except RuntimeError as e:
        print(f"Error: {e}")
    finally:
        os.chdir(original_cwd)


def get_size_in_mb(path):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(os.path.expanduser(path)):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if os.path.isfile(fp):
                total_size += os.path.getsize(fp)
    return total_size / (1024 * 1024)


def run_size_comparison():
    start_time = time.time()
    try:
        cha_size = get_size_in_mb("~/.cha/venv/") + get_size_in_mb(
            "~/.cache/whisper/tiny.pt"
        )
        ch_size = get_size_in_mb("~/.ch")
    except Exception as e:
        print(e)
        sys.exit(1)
    if cha_size < ch_size:
        ratio = ch_size / cha_size
        ratio_str = f"cha is {ratio:.4f}x smaller than ch"
    else:
        ratio = cha_size / ch_size
        ratio_str = f"ch is {ratio:.4f}x smaller than cha"
    runtime = time.time() - start_time
    print(f"cha size: {cha_size:.4f} MB")
    print(f"ch size: {ch_size:.4f} MB")
    print(f"{ratio_str}")
    print(f"{runtime:.4f} seconds runtime")


def _over_all_startup_time_compare(
    command_path, prompt, shell, timeout, poll_interval, debug_mode, total_runs
):
    times = []
    for i in range(total_runs):
        try:
            t = measure_startup_time(
                command=command_path,
                prompt=prompt,
                shell=shell,
                timeout=timeout,
                poll_interval=poll_interval,
            )
            if t is None:
                if debug_mode:
                    print("Prompt not detected")
            else:
                if debug_mode:
                    print(f"Startup time: {t:.4f} seconds")
                times.append(t)
        except TimeoutError as e:
            if debug_mode:
                print(e)
    if times:
        avg = sum(times) / len(times)
        if debug_mode:
            print(f"{total_runs} total runs for '{os.path.basename(command_path)}'")
            print(f"Averaged {avg:.4f} seconds")
        return avg
    else:
        if debug_mode:
            print("No successful runs to average.")
        return None


def _run_measurement_compare(
    command,
    prompt,
    shell,
    timeout,
    poll_interval,
    return_dict,
    key,
    total_runs,
    debug_mode,
):
    avg_time = _over_all_startup_time_compare(
        command_path=command,
        prompt=prompt,
        shell=shell,
        timeout=timeout,
        poll_interval=poll_interval,
        debug_mode=debug_mode,
        total_runs=total_runs,
    )
    return_dict[key] = avg_time


def run_startup_comparison():
    total_runs = 100
    prompt = "User:"
    shell = "/bin/zsh"
    timeout = 5
    poll_interval = 0.01
    debug_mode = False
    start_time = time.time()
    manager = multiprocessing.Manager()
    return_dict = manager.dict()
    p1 = multiprocessing.Process(
        target=_run_measurement_compare,
        args=(
            "ch",
            prompt,
            shell,
            timeout,
            poll_interval,
            return_dict,
            "ch",
            total_runs,
            debug_mode,
        ),
    )
    p2 = multiprocessing.Process(
        target=_run_measurement_compare,
        args=(
            "cha",
            prompt,
            shell,
            timeout,
            poll_interval,
            return_dict,
            "cha",
            total_runs,
            debug_mode,
        ),
    )
    p1.start()
    p2.start()
    p1.join()
    p2.join()
    ch_avg = return_dict.get("ch")
    cha_avg = return_dict.get("cha")
    if ch_avg is None or cha_avg is None:
        sys.exit(1)
    if ch_avg < cha_avg:
        ratio = cha_avg / ch_avg if ch_avg > 0 else float("inf")
        ratio_str = f"ch is {ratio:.4f}x faster then cha"
    else:
        ratio = ch_avg / cha_avg if cha_avg > 0 else float("inf")
        ratio_str = f"cha is {ratio:.4f}x faster then ch"
    runtime = time.time() - start_time
    print(f"cha = {cha_avg:.4f} seconds ({total_runs} runs)")
    print(f"ch = {ch_avg:.4f} seconds ({total_runs} runs)")
    print(ratio_str)
    print(f"{runtime:.4f} seconds runtime")


def run_line_count():
    cha_root_dir = str(
        "/".join(os.path.dirname(os.path.abspath(__file__)).split("/")[:-2]) + "/"
    )

    count_lines_by_extension(
        directory=cha_root_dir,
        ext_targets=[".py", ".sh", ".md", ".json"],
        show_largest_file=True,
        show_file_count=True,
    )


def run_startup_time():
    over_all_startup_time(command_path="cha", debug_mode=False, total_runs=30)


def run_dependencies():
    cha_root_dir = str(
        "/".join(os.path.dirname(os.path.abspath(__file__)).split("/")[:-2]) + "/"
    )

    packages = depends_count(cha_root_dir)
    newline_packages = "\n".join(packages)
    os.system(f'echo "{newline_packages}" | column')
    print(f"\nTotal Dependencies: {len(packages)}")


def run_git_stats():
    cha_root_dir = str(
        "/".join(os.path.dirname(os.path.abspath(__file__)).split("/")[:-2]) + "/"
    )

    analyze_git_repository(cha_root_dir)


def run_all_tests():
    cha_root_dir = str(
        "/".join(os.path.dirname(os.path.abspath(__file__)).split("/")[:-2]) + "/"
    )

    print(underline("Cha Line Count") + "\n")
    count_lines_by_extension(
        directory=cha_root_dir,
        ext_targets=[".py", ".sh", ".md", ".json"],
        show_largest_file=True,
        show_file_count=True,
    )

    print("\n" + underline("Cha Startup Time") + "\n")
    over_all_startup_time(command_path="cha", debug_mode=False, total_runs=30)

    print("\n" + underline("Cha's Dependencies") + "\n")
    packages = depends_count(cha_root_dir)
    newline_packages = "\n".join(packages)
    os.system(f'echo "{newline_packages}" | column')
    print(f">>> Total Dependencies: {len(packages)}")

    print("\n" + underline("Cha's Git Stats") + "\n")
    analyze_git_repository(cha_root_dir)


if __name__ == "__main__":
    try:
        parser = argparse.ArgumentParser(
            description="Cha Toolkit - Run various analysis tests on the Cha project",
            add_help=False,
        )
        parser.add_argument(
            "-h",
            "--help",
            action="help",
            default=argparse.SUPPRESS,
            help="Show this help message and exit",
        )
        parser.add_argument(
            "-l",
            "--lines",
            action="store_true",
            help="Count lines by file extension",
        )
        parser.add_argument(
            "-s",
            "--startup",
            action="store_true",
            help="Measure startup time performance",
        )
        parser.add_argument(
            "-d",
            "--deps",
            action="store_true",
            help="List project dependencies",
        )
        parser.add_argument(
            "-g",
            "--git",
            action="store_true",
            help="Show git repository statistics",
        )
        parser.add_argument(
            "-a",
            "--all",
            action="store_true",
            help="Run all tests (default if no specific test is selected)",
        )
        parser.add_argument(
            "--compare-sizes",
            action="store_true",
            help="Compare cha and ch installation sizes",
        )
        parser.add_argument(
            "--compare-startups",
            action="store_true",
            help="Compare cha and ch startup times",
        )

        args = parser.parse_args()

        specific_tests = [
            args.lines,
            args.startup,
            args.deps,
            args.git,
            args.all,
            args.compare_sizes,
            args.compare_startups,
        ]
        any_specific_test = any(specific_tests)

        if not any_specific_test:
            parser.print_help()
        elif args.all:
            run_all_tests()
        else:
            if args.lines:
                run_line_count()
            if args.startup:
                run_startup_time()
            if args.deps:
                run_dependencies()
            if args.git:
                run_git_stats()
            if args.compare_sizes:
                run_size_comparison()
            if args.compare_startups:
                run_startup_comparison()

    except (KeyboardInterrupt, EOFError):
        print()
    except SystemExit:
        pass
