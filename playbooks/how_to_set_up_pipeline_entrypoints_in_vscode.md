# Playbook: Set Up Host VS Code Pipeline Entrypoints

## Use when

Creating or reviewing a host pipeline's VS Code actions.

## Load

`AGENTS.md`; host README, pipeline contract, CLI help, VS Code/native scripts,
`scripts/bootstrap.py`, selected bootstrap version and dependencies. Load bootstrap
maintenance instructions when needed, and `templates/vscode/` examples selectively.

Do not infer the host's entrypoints from the framework reference CLI.
Use deterministic inventory and configuration checks.

## Procedure

1. Inventory host actions, required inputs, platforms and recovery/mutation behavior.
2. Preserve existing files; resolve material ambiguity with the host user.
3. Select exactly one ordinary, non-recovery canonical pipeline action.
4. Use host-owned native wrappers under declared source roots. Locate Python,
   bootstrap once, then execute the operation only on success. Preserve failures
   and cancellation. Do not invent a package manager, elevate, modify system
   Python or assume dependency layouts.
5. Give every declared action a visible `tasks.json` process task with argument
   arrays, operator inputs, platform dispatch and foreground terminal output.
6. Add the canonical pipeline to `launch.json` using the same native path, once.
   Never repeat the full operation through both pre-launch task and launch command.
7. For software-build stages, use `references/source_build_governance.md`: both
   task and launch paths must reach the blocking source check before building.
   Adapt `software-build.*` examples only where software building is required.
   Do not invent software builds for analysis pipelines or create hosted workflows.
8. Merge approved host-specific configuration; never replace the file from a framework example.
9. Verify syntax, task coverage, inputs, platform dispatch, bootstrap/gate order,
   one canonical action and execution, cancellation and failure propagation.
   Test that invalid source prevents software-build execution.

Direct host-owned CLI and scheduler entrypoints remain supported.

## Outputs and stop conditions

Record the host inventory, task/launch/native-path mapping and local evidence.
Resolve unsupported platforms, unsafe prerequisites, privileges, uncertain paths,
credentials or destructive overwrites before dependent work.
