# Playbook: Optimize VS Code and Cerebras

## Use when

Optimizing an existing Cerebras Custom Endpoint in VS Code Chat with named Qwen 3.8 27B reasoning presets.

## Load

The installed VS Code/Copilot Chat version, the operator-selected `chatLanguageModels.json` in its actual profile/remote scope, and [the configuration reference](../references/vscode_cerebras_reasoning_presets.md). Read configuration without resolving or displaying credentials.

## Prerequisite

The user must already have added a Custom Endpoint through VS Code and supplied the Cerebras API key through its credential UI. Require an existing `apiKey` input reference backed by that scope's secret storage. An empty starter model is acceptable; missing credentials are not. Stop and direct the user to complete UI setup if this prerequisite fails. Never create secret IDs, request a key in chat, or copy another host's reference.

## Procedure

1. Confirm the active JSON path using the reference's Windows/Linux locations and provider UI. Bind edits to the approved scope; preserve unrelated providers and make a local backup. Identify the intended Cerebras entry explicitly when multiple candidates exist.
2. Follow the reference to create `cerebras-qwen3.8:27b-low`, `cerebras-qwen3.8:27b-medium`, and `cerebras-qwen3.8:27b-high`. Copy the existing secret reference verbatim into each provider. Keep the API model ID `qwen-3.8-27b`; aliases are display names.
3. Set every preset's total context to 128144, reserving 16000 output tokens. Use the installed provider's supported request-shaping mechanism; never infer effort from a name or silently retain an unsupported field.
4. Validate JSON, distinct names, matching secret references, explicit effort, budgets and preserved unrelated entries. Merge existing matching presets rather than duplicate them.
5. Select medium for ordinary interactive work. Verify each preset with a sanitized bounded chat and inspect redacted outgoing model/effort metadata. Measure representative latency and answer fitness before claiming improvement; choose low/high according to observed task needs.

## Output and stop conditions

Record version, scope, presets, budgets, redacted verification and rollback location. Stop on missing secret storage, unsupported request shaping, account context limits below the requested cap, alias collisions or effort mismatches. Restore only affected entries from backup on failure. Configuration checks alone establish no live performance result.
