---
plan_id: 2026-10-18-00-10-00_host-owned-build-governance
title: Correct governance to host-owned VS Code pipelines
summary: Remove unauthorized GitHub Actions integration and apply software-build gates through host-owned VS Code entrypoints.
status: current
created_at: 2026-10-18-00-10-00
---

# Correct governance to host-owned VS Code pipelines

Key: `[ ]` pending task, `[x]` completed task, `[?]` needs validation, `[-]` closed task

Authority: the user explicitly directs removing all GitHub Actions integration. Agentic Pipelines supplies reusable instructions and helpers; the host defines its environment and pipeline, which may build software or perform data analysis. Software-build checks belong in applicable host pipelines, with VS Code tasks and the canonical entrypoint in launch.json. This instruction supersedes the CI requirements in the previous source-governance plan. No further approval is needed for this correction and publication.

- [x] C1. Remove both checked-in Actions workflows, Actions checker code/configuration and workflow-specific tests.
- [x] C2. Correct canonical policy, routing, design/bootstrap procedures and README to preserve host/environment ownership and condition software-build integration on an actual software build.
- [x] C3. Provide adaptable VS Code software-build task/launch/native-wrapper examples that bootstrap once and stop before building on source failure.
- [x] C4. Verify source checks, staged commit hook, VS Code mappings, blocked build behavior and relevant framework regression tests locally; no hosted workflow work.
- [ ] C5. Record the supersession and journal, archive this plan, publish upstream, and commit/push only the parent framework pointer and scoped correction receipt.

Boundary: preserve prior source decomposition and generic checker/hook/build helpers. Do not modify runtime source, host VS Code files or unrelated parent work. This framework has no governing roadmap; no runtime scope, dates or delivery commitments change.

## Verification

123 local tests OK, one optional renderer-module skip; 66 source files pass. Native PowerShell fixture proves bootstrap-before-gate, invalid source prevents build execution, a valid build preserves status 7, and bootstrap failure preserves status 9 without building. Task and launch examples target one shared native path. Generic blocked-build and staged-hook regressions pass. Both workflow files and the Actions auditing module are removed; no workflow registry is required. No hosted jobs or remote administration were used for this correction.
