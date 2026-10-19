# Playbook: Optimize VS Code and Cerebras

## Use when

Configuring an existing Cerebras Custom Endpoint in VS Code Chat with the native Thinking Effort selector.

## Load

The installed VS Code/Copilot Chat version, the operator-selected `chatLanguageModels.json` in its actual profile/remote scope, and [the configuration reference](../references/vscode_cerebras_reasoning_presets.md). Read configuration without resolving or displaying credentials.

## Prerequisite

The user must already have added a Custom Endpoint through VS Code and supplied the Cerebras API key through its credential UI. Require an existing `apiKey` input reference backed by that scope's secret storage. An empty starter model is acceptable; missing credentials are not. Stop and direct the user to complete UI setup if this prerequisite fails. Never create secret IDs, request a key in chat, or copy another host's reference.

## Procedure

1. Confirm the active JSON path using the reference's Windows/Linux locations and provider UI. Bind edits to the approved scope; preserve unrelated providers and make a local backup. Identify the intended Cerebras entry explicitly when multiple candidates exist.
2. Configure one Cerebras provider/model entry using API model ID `qwen-3.8-27b`. Preserve its existing secret reference. Model-level `thinking: true`, `supportsReasoningEffort: ["none", "low", "medium", "high"]`, and `reasoningEffortFormat: "chat-completions"` are mandatory. Use the native selector to change effort.
3. Confirm the account/model context and completion limits. Preserve approved budgets; the reference's operator example uses 131072 total tokens and 40960 output tokens, leaving 90112 input tokens. These numbers require account/model verification.
4. Validate JSON, selector fields, model identity, secret reference, budget arithmetic and preservation of unrelated entries. Update the existing entry rather than duplicate it. Remove conflicting fixed effort request options from the selected entry so the selector governs the request.
5. Select the model and choose Thinking Effort in its picker submenu. Start with medium for ordinary interactive work. Verify none/low/medium/high with bounded sanitized requests and redacted outgoing model/effort metadata. Measure representative latency and answer fitness before claiming improvement.

## Output and stop conditions

Record version, scope, selector values, budgets, redacted verification and rollback location. Stop on missing secret storage, unsupported selector/request shaping, account limits below the requested budgets or outgoing effort mismatches. Restore only affected entries from backup on failure. Configuration checks alone establish no live performance result.
