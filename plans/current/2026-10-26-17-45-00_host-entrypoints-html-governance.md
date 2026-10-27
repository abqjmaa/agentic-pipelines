---
plan_id: 2026-10-26-17-45-00_host-entrypoints-html-governance
title: Preserve governed host entrypoints and parse HTML comments
summary: Narrow R11 repair for explicitly declared root launchers and HTML source accounting without weakening limits or inventories.
status: current
created_at: 2026-10-26-17-45-00
---

# Host entrypoints and HTML governance

Authorized by runtime operator October 26: repair in owning framework repo,
publish dependency before advancing runtime pointer; preserve all enforcement.
Host root bootstrap.sh is a documented stable dispatcher. Framework host
preservation instructions conflict with the checker rejecting every root file.
HTML is included in SOURCE_SUFFIXES but no available adapter recognizes HTML
comments. Confirmed using bounded valid-header and undeclared-launcher cases.

Key: `[ ]` pending task, `[x]` completed task, `[?]` needs validation, `[-]` closed task

- [x] Confirm defects against host contract and existing checker.
- [x] Add exact root-entrypoint declaration with purpose/delegate, normal language/size checks and root README inventory; reject wildcards, traversal, undeclared files and invalid targets.
- [x] Add HTML-aware comment accounting; retain executable/data/attribute content, inspect embedded script/style and refuse unsupported inline executable attributes.
- [x] Test worktree/staged checks, valid cases and genuine size/inventory/layout failures, and build refusal.
- [x] Update framework policy/README/config documentation; run focused and full tests and source gate.
- [ ] Commit/publish dependency; verify remote receipt before runtime pin advances.

No host entrypoint, model policy, data or live service is changed here.

Verification: 78 focused tests passed (1 skip); canonical source check 68 files,
zero failures. Full suite: 165 tests, one existing failure and two skips;
Cerebras playbook is 363 words at unchanged upstream HEAD `9847070`, exceeding
the pre-existing test's <350 rule. No unrelated guidance changed.
Publication is authorized by the runtime operator; receipt follows push.
