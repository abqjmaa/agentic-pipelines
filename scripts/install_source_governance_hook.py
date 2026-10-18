#!/usr/bin/env python3
"""
Install or check a staged source gate while preserving an existing pre-commit hook.
Honor repository hooksPath and chain the saved hook only after governance passes.
Writes only the selected repository's hook directory; never changes Git auth.
"""

import argparse
from pathlib import Path
import shlex
import subprocess
import sys


MARKER = "# Agentic Pipelines staged source governance v1"


def main():
    parser = argparse.ArgumentParser(description="Install/check staged source governance")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    root = args.repo_root.resolve()
    output = subprocess.check_output(
        ["git", "-C", str(root), "rev-parse", "--git-path", "hooks"], text=True,
    ).strip()
    directory = Path(output)
    if not directory.is_absolute():
        directory = root / directory
    hook = directory / "pre-commit"
    backup = directory / "pre-commit.before-source-governance"
    checker = Path(__file__).resolve().with_name("check_source_governance.py")
    python = shlex.quote(Path(sys.executable).as_posix())
    command = f"{python} {shlex.quote(checker.as_posix())} --repo-root {shlex.quote(root.as_posix())} --staged"
    saved = shlex.quote(backup.resolve().as_posix())
    expected = f'#!/bin/sh\n{MARKER}\n{command} || exit $?\nif [ -f {saved} ]; then\n  exec {saved} "$@"\nfi\n'
    if hook.is_symlink():
        raise ValueError("pre-commit is a symlink; compose the gate in its owner instead")
    current = hook.read_text(encoding="utf-8") if hook.exists() else ""
    if current == expected:
        print("source governance hook: PASS")
        return 0
    if args.check:
        print("source governance hook: missing or stale", file=sys.stderr)
        return 1
    directory.mkdir(parents=True, exist_ok=True)
    if current and MARKER not in current:
        if backup.exists():
            raise ValueError("existing saved hook prevents replacement; compose without discarding either hook")
        hook.rename(backup)
    hook.write_text(expected, encoding="utf-8", newline="\n")
    hook.chmod(hook.stat().st_mode | 0o111)
    print("source governance hook: installed; existing hook preserved")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print(f"source governance hook: FAIL: {error}", file=sys.stderr)
        raise SystemExit(1)
    except KeyboardInterrupt:
        print("source governance hook: interrupted", file=sys.stderr)
        raise SystemExit(130)
