# Govern source and builds

## Use when

Organizing source or enforcing commit/build gates.

## Load

Read `references/source_build_governance.md` and the approved implementation plan.

## Procedure

1. Inventory owned source and every build entrypoint; preserve existing work.
2. Declare root directories, language adapters and comment patterns under `code`
   in tracked `api.sample.yaml` and local ignored `api.yaml`. Never overwrite local
   inference credentials. Unsupported adapters need implementation and fixtures.
3. Decompose oversized files by responsibility. Add accurate multiline file
   headers and a README inventory in every source directory. Expand combined
   statements; preserve behavior through focused regression tests.
4. Add the canonical failing source check to **every build pipeline** before its
   build commands. Register build pipelines in the public code configuration.
   For Actions use a step named `Source governance` with
   `run: python scripts/check_source_governance.py --repo-root .` (prefix the
   script with the framework submodule path in a host). No conditional/advisory
   gate or ignored status. For other systems use the governed-build wrapper and
   prove a deliberately invalid source tree prevents command execution.
5. Install the staged pre-commit gate through the host's selected bootstrap,
   preserving existing hooks. Check committed content independently in CI.
   Configure required remote checks where authorized; report missing protection.
6. Run source checks, staged-snapshot checks, failure-injection fixtures and
   relevant behavior regressions. Never loosen the cap or hide source to pass.
7. Reconcile plan/status and journal. Publish the framework, then update host pins.
   Host source/build migration is separate work and requires its own evidence.

The user's implementation authorization covers routine fixes and verification;
do not introduce per-file or per-phase permission stops within that scope.
