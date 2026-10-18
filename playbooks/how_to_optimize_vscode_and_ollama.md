# Playbook: Optimize VS Code and Ollama

## Use when

Tuning local VS Code Chat, target/draft Q8 caches, context aliases, inference timeouts and warm-prefix reuse.

## Load

`AGENTS.md`, applicable host configuration, and the complete
`references/vscode_ollama_configuration.md` procedure before taking action.

## Required behavior

Require Q8 for target and active draft K/V caches, preserve MTP, and verify separate allocations. Flash Attention is conditional on hardware/backend support; unsupported FA alone does not block work. Require effective 45-minute inference waits with immediate cancellation. Preserve full model definitions and host residency policy.

## Procedure

1. Read the linked reference; it retains all configuration examples, evidence requirements and stop conditions.
2. Identify the actual host, provider/version, failure signature and existing setup.
3. Follow the reference in order within the approved task scope. Preserve host settings and secrets.
4. Verify the requested outcome using retained, sanitized evidence. Distinguish configuration from live verification.
5. Record the result and exact remaining blocker without claiming unsupported success.
