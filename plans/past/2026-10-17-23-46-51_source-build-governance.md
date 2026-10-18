---
plan_id: 2026-10-17-23-46-51_source-build-governance
title: Enforce source and build governance
summary: Establish canonical modular source policy, deterministic checks, staged commit checks, and mandatory failing build gates.
status: past
created_at: 2026-10-17-23-46-51
---

# Enforce source and build governance

Key: `[ ]` pending task, `[x]` completed task, `[?]` needs validation, `[-]` closed task

Authority: the user's October 17 instruction approves implementation and upstream publication of the discussed rules, including a failing gate in every build pipeline. No further phase approval is required within this scope.

- [x] G1. Establish canonical policy and reproducible configuration.
  - [x] G1.1 Route mandatory source/build policy from AGENTS and maintenance/bootstrap/build playbooks.
  - [x] G1.2 Define code roots, comment patterns, inclusive 400-line accounting, file headers and README inventories in tracked api.sample.yaml; validate local api.yaml without inference credentials.
- [x] G2. Implement deterministic enforcement.
  - [x] G2.1 Implement recursive source inventory, language-aware accounting and Python statement checks with actionable failures.
  - [x] G2.2 Check staged snapshots before commits without running staged executable code; preserve existing hooks.
  - [x] G2.3 Gate arbitrary build commands and every framework CI job; propagate failures and document host integration requirements.
- [x] G3. Make the framework comply.
  - [x] G3.1 Decompose runner, state and evidence modules by responsibility while preserving public interfaces.
  - [x] G3.2 Add accurate module headers and directory inventories; expand compressed statements.
- [x] G4. Validate and publish.
  - [x] G4.1 Test boundaries, comment/string distinctions, roots, documentation, staged snapshots and blocked builds.
  - [x] G4.2 Run framework regression suite, source gate and diff checks; install and exercise hook.
  - [x] G4.3 Update journal and indexes, publish framework upstream and refresh parent pointer.

Scope boundary: this checkpoint implements and self-applies reusable framework governance. Runtime source decomposition and host-specific build adoption remain explicit runtime work; a pointer refresh alone does not establish host compliance. No roadmap exists in this framework; this plan is its scoped implementation authority. The parent runtime roadmap is not changed by this framework-only capability.

## Local verification checkpoint

64 source files pass; largest file has 351 counted lines. Full standard-environment suite: 120 tests, OK with one optional renderer-module skip. Existing renderer environment: all 12 renderer tests pass separately. Includes 33 new source/hook/build regressions. Worktree checks, diff checks, and installed hook --check pass. Existing provider/runner/state/evidence behavior tests pass after responsibility-based extraction. Two preexisting overlong routed playbooks were composed with linked references, preserving their complete guidance rather than weakening the existing size test.

CI is checked in for every framework Actions build job. Remote required-branch protection is an administrative setting, not established by these files. Hosts still need explicit source/configuration/bootstrap/build adoption; this checkpoint does not claim EBE, Pi, or parent source compliance.

## Publication receipt

Implementation published upstream as `8ef7c5e7dfa66d13d3d050ddbc3a9f033fa1f1c2`; installed staged hook passed during the actual commit. Parent framework checkout/pointer advanced; the parent publication checkpoint records the final documentation commit. Actions started: source governance run 39105972173 and PDF matrix run 39105972170. Final remote results belong in the parent publication receipt. The connected GitHub integration returned 403 for branch-protection inspection; host gh is not configured. No credentials were changed and no claim of required branch protection is made. Repository owner must configure/verify required governance checks through an administrative connection.
