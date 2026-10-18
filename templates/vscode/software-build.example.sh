#!/usr/bin/env bash
# Bootstrap declared host prerequisites, then gate the host software build.
# Adapt into a declared host scripts root and replace command markers from its environment.
# Both VS Code task and launch entrypoints use this same failing build path.
set -euo pipefail

trap 'printf "%s\n" "build: interrupted" >&2; exit 130' INT

if ! command -v REPLACE_PYTHON_COMMAND >/dev/null 2>&1; then
  printf '%s\n' 'build: host Python is unavailable' >&2
  exit 1
fi

REPLACE_PYTHON_COMMAND -B "$(dirname "$0")/bootstrap.py"

exec REPLACE_PYTHON_COMMAND -B "$(dirname "$0")/../agentic-pipelines/scripts/governed_build.py" --repo-root "$(dirname "$0")/.." -- REPLACE_BUILD_COMMAND "$@"
