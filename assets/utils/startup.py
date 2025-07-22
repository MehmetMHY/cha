import subprocess
import signal
import select
import time
import os


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


def main(command_path, debug_mode=False, total_runs=15):
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


if __name__ == "__main__":
    debug_mode = False
    total_runs = 30
    command_to_time = "cha"

    try:
        debug_input = input(f"Debug mode (current: {debug_mode}): ").strip()
        if debug_input.lower() in ["true", "false"]:
            debug_mode = debug_input.lower() == "true"

        runs_input = input(f"Total runs (current: {total_runs}): ").strip()
        if runs_input.isdigit():
            total_runs = int(runs_input)

        command_input = input(f"Command path (current: {command_to_time}): ").strip()
        if command_input:
            command_to_time = command_input

        main(command_path=command_to_time, debug_mode=debug_mode, total_runs=total_runs)
    except (KeyboardInterrupt, EOFError):
        print()
        exit(0)
