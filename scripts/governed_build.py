#!/usr/bin/env python3
"""
Gate an arbitrary build command with the canonical source governance check.
Execute the command only after a passing tree check and propagate its exit status.
The caller declares dependencies and command; this wrapper installs nothing.
"""

import argparse
from pathlib import Path
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(description="Fail closed before a build")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command
    if command and command[0] == "--":
        command = command[1:]
    if not command:
        parser.error("a build command is required after --")
    checker = Path(__file__).with_name("check_source_governance.py")
    print("build: checking source governance", flush=True)
    status = subprocess.call([sys.executable, str(checker), "--repo-root", str(args.repo_root)])
    if status:
        print("build: blocked by source governance", file=sys.stderr)
        return status
    print("build: source governance passed; executing command", flush=True)
    return subprocess.call(command, cwd=args.repo_root)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("build: interrupted", file=sys.stderr)
        raise SystemExit(130)
