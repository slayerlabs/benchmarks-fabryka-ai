"""Run a command (one RULER prepare.py call) under a wall-clock limit; portable, macOS has no `timeout`.

Usage: python prepare_limited.py <seconds> <command...>
Exit code: the command's, or 124 when the limit passed. On timeout the whole process group is killed: prepare.py
starts the task's generator script through a shell, and that generator is what loops (RULER db43f92
scripts/data/synthetic/qa.py L196-206 never exits when even its smallest document set exceeds the length).
"""

import os
import signal
import subprocess
import sys


def main():
    limit, command = float(sys.argv[1]), sys.argv[2:]
    process = subprocess.Popen(command, start_new_session=True)
    try:
        sys.exit(process.wait(timeout=limit))
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGKILL)
        process.wait()
        print(f"prepare_limited.py: no result after {limit:.0f} s, killed: {' '.join(command[:4])} ...", file=sys.stderr)
        sys.exit(124)


if __name__ == "__main__":
    main()
