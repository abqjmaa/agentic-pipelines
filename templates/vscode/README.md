# VS Code Entrypoint Examples

These files illustrate the required host-owned shape; they are not installable framework defaults. Replace every `REPLACE_...` and `PATH_TO_...` value from the host's reviewed entrypoint, prerequisite, and platform contracts. Merge approved fields into existing host files instead of replacing them.

- `tasks.example.json` demonstrates one task per example entrypoint, argument arrays, visible foreground terminals, inputs, and Windows versus Linux/macOS native dispatch.
- `launch.example.json` demonstrates one primary play action that invokes one native wrapper once. It uses VS Code's built-in JavaScript Debug Terminal (`node-terminal`) only to expose an arbitrary terminal command through the play button; it does not make Node.js a pipeline prerequisite.
- `bootstrap.example.ps1` and `bootstrap.example.sh` demonstrate locating the host's Python interpreter, invoking its stable `scripts/bootstrap.py` once, and delegating only after success. Put source wrappers under a declared host source root such as `scripts/`; adjust paths for that layout. Keep `.vscode/` for task/launch configuration. They intentionally do not install software themselves.

Schema basis checked 2026-08-04: [VS Code tasks schema](https://code.visualstudio.com/docs/reference/tasks-appendix), [platform-specific launch properties](https://code.visualstudio.com/docs/debugtest/debugging-configuration#_platformspecific-properties), and the official [`node-terminal` command option](https://github.com/microsoft/vscode-js-debug/blob/main/OPTIONS.md#node-terminal-launch).

## Optional host software-build examples

Only use `software-build.*` when the host has a software-build pipeline. Merge
`software-build.tasks.example.json` into host tasks and, when building is the
canonical operation, merge `software-build.launch.example.json` into host launch
configuration. Both refer to the same adapted `software-build.example.sh` or
`.ps1` wrapper under a declared source root such as host `scripts/`: locate host Python, bootstrap once, invoke `governed_build.py`,
then run the host-selected build command only if source checks pass. Replace
markers and adapt wrapper/submodule paths to the host. A mixed pipeline keeps its
canonical main action and invokes this gate only at its software-build stage.
Do not create a software build for an analysis-only pipeline. No host file is
installed or overwritten by these examples.

## Source inventory

- `bootstrap.example.ps1`: Bootstrap host prerequisites and forward the declared pipeline command and failures.
- `bootstrap.example.sh`: Bootstrap host prerequisites and forward the declared pipeline command and failures.

- `software-build.example.ps1`: Bootstrap host prerequisites and gate a host-selected software build, propagating failure.
- `software-build.example.sh`: Bootstrap host prerequisites and gate a host-selected software build, propagating failure.
