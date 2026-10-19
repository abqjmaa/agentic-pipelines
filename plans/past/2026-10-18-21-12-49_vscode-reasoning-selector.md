---
plan_id: 2026-10-18-21-12-49_vscode-reasoning-selector
title: VS Code reasoning selector guidance
summary: Require Cerebras reasoning selector fields, remove effort aliases, and document Ollama feasibility.
status: past
created_at: 2026-10-18-21-12-49
---

# VS Code reasoning selector guidance

Key: `[ ]` pending task, `[x]` completed task, `[?]` needs validation, `[-]` closed task

- [x] 1. Replace Cerebras effort aliases with one model and the native selector.
  - [x] 1.1 Require `thinking: true`, `supportsReasoningEffort: ["none", "low", "medium", "high"]`, and `reasoningEffortFormat: "chat-completions"` in the Cerebras playbook.
  - [x] 1.2 Replace alias instructions and examples in the Cerebras reference with one provider/model; retain credential boundaries and make budgets explicit using the supplied 131072 total and 40960 output configuration as an operator example, subject to provider/account verification.
  - [x] 1.3 Update the playbooks README description and AGENTS routing description consistently.
- [x] 2. Document Ollama feasibility without changing user configuration.
  - [x] 2.1 Add the official extension's `ollama.thinkingLevels` mechanism and its lack of native effort selector support to the Ollama reference; explain Custom Endpoint feasibility through Ollama's OpenAI-compatible API, requiring model/server verification.
- [x] 3. Verify and checkpoint.
  - [x] 3.1 Parse replacement JSON examples, check budget arithmetic, links, and removal of Cerebras effort-alias instructions; review the scoped diff.
  - [x] 3.2 Update this plan, regenerate indexes, and record evidence and remaining live-verification limits in the journal.

## Authority and roadmap

User requested these documentation changes and an Ollama feasibility investigation. User approved implementation and requested committing everything and pushing. No governing roadmap was found; no roadmap alignment can be certified. The two current plans concern PDF rendering and credentials and do not cover this scope.

## Read-only evidence

- Local default-profile `chatLanguageModels.json` matches the supplied configuration; secret reference existence checked without resolution. No configuration edits or live inference performed.
- Installed official Ollama extension 0.0.13: `package.json` declares `ollama-models`, URL, string-array model filtering, and `ollama.thinkingLevels`; `out/provider.js` reads that setting and sends native `think`; no selector-field handling found.
- Microsoft selector contract: https://code.visualstudio.com/docs/agent-customization/language-models
- Cerebras accepted effort values: https://inference-docs.cerebras.ai/capabilities/reasoning
- Official Ollama extension README explicitly describes native dropdown as future work due to proposed API constraints: https://github.com/ollama/ollama-vscode/blob/main/README.md
- Ollama compatibility contract: https://docs.ollama.com/api/openai-compatibility

## Expected files

`playbooks/how_to_optimize_vscode_and_cerebras.md`, `references/vscode_cerebras_reasoning_presets.md`, `playbooks/README.md`, `AGENTS.md`, `references/vscode_ollama_configuration.md`, plan/index files, and today's journal. No user-profile edits, extension installation, or inference calls. User additionally authorized committing all changes and pushing.

## Verification receipt

Cerebras JSON and both Ollama JSON examples parse; selector values and 90112 input budget assertions pass; relative reference links resolve. Source governance passes all 66 files with zero failures. Whitespace diff check passes. Host git ls-remote origin HEAD succeeds. No live inference or performance claim. User approved implementation, commit and push. Plan archived after documentation completion; publication follows in the same checkpoint.
