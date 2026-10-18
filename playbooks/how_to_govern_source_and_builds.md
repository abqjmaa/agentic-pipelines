# Govern source and software builds

## Use when

Organizing source or adding governance to a host's software-build pipeline.

## Load

`references/source_build_governance.md`, the approved plan, host pipeline contract,
and `playbooks/how_to_set_up_pipeline_entrypoints_in_vscode.md` when adding entrypoints.

## Procedure

1. Identify the host's actual pipeline type, environment and source. The framework
   submodule supplies instructions/helpers; it is not itself the host pipeline.
2. Declare source roots, language adapters and comment patterns under `code` in
   tracked `api.sample.yaml` and local ignored `api.yaml`. Preserve credentials.
3. Decompose oversized files by responsibility, document files/directories, and
   expand combined statements. Verify behavior with appropriate regressions.
4. Install/check the staged pre-commit integration through host bootstrap,
   preserving existing hooks. Run the source check before commits.
5. If the host includes software building, make every actual software-build path
   run the canonical source check and stop on failure. Use `governed_build.py` or
   propagate the canonical check's nonzero status from the host's build script.
   Do not invent software building for analysis or other pipelines without it.
6. Expose host actions as visible VS Code tasks. Add the canonical pipeline to
   `launch.json`; both surfaces use the same native bootstrap/operation path.
   Software builds must reach the failing gate through both surfaces, once.
   Adapt the software-build examples only where applicable; preserve host files.
7. Verify locally that failed source checks prevent command execution and passing
   checks preserve build results. Verify task/launch mappings and bootstrap order.
8. Reconcile plan/status and journal, then publish. Record host adoption separately
   from framework pointer updates. Do not add GitHub Actions integration or remote
   administration requirements.

Existing implementation authorization covers routine corrections and verification;
do not introduce per-file or per-phase permission stops within that scope.
