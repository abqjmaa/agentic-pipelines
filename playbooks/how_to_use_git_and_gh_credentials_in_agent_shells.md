# Playbook: Use git and gh Credentials in Agent Shells

## Use when

Investigating authenticated Git/gh failures in agent sessions.

## Load

`AGENTS.md`, applicable host configuration, and the complete
`references/git_gh_host_credentials.md` procedure before taking action.

## Required behavior

Run authenticated checks and operations in the actual host terminal using its existing credential store. A sandbox failure never proves credentials expired. Distinguish network, permission and credential errors; never weaken injected noninteractive or repository safety settings. Do not print, stage or request secrets in chat.

## Procedure

1. Read the linked reference; it retains all configuration examples, evidence requirements and stop conditions.
2. Identify the actual host, provider/version, failure signature and existing setup.
3. Follow the reference in order within the approved task scope. Preserve host settings and secrets.
4. Verify the requested outcome using retained, sanitized evidence. Distinguish configuration from live verification.
5. Record the result and exact remaining blocker without claiming unsupported success.
