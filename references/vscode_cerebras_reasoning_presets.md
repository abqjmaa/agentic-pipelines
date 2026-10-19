# VS Code Cerebras reasoning selector

Use with [the optimization playbook](../playbooks/how_to_optimize_vscode_and_cerebras.md).

## Locate chatLanguageModels.json

These are likely locations for desktop VS Code. The file belongs to the active user profile; use the exact case `chatLanguageModels.json` on Linux.

| Installation / profile | Windows | Linux |
| --- | --- | --- |
| Stable, default profile | `%APPDATA%\Code\User\chatLanguageModels.json` | `~/.config/Code/User/chatLanguageModels.json` |
| Stable, named profile | `%APPDATA%\Code\User\profiles\<profile-id>\chatLanguageModels.json` | `~/.config/Code/User/profiles/<profile-id>/chatLanguageModels.json` |
| Insiders, default profile | `%APPDATA%\Code - Insiders\User\chatLanguageModels.json` | `~/.config/Code - Insiders/User/chatLanguageModels.json` |
| Insiders, named profile | `%APPDATA%\Code - Insiders\User\profiles\<profile-id>\chatLanguageModels.json` | `~/.config/Code - Insiders/User/profiles/<profile-id>/chatLanguageModels.json` |

For example, a standard Windows install for CJ usually uses `C:\Users\CJ\AppData\Roaming\Code\User\chatLanguageModels.json`. A native Linux desktop session on thor-2 usually uses `/home/<user>/.config/Code/User/chatLanguageModels.json`. `<profile-id>` is the directory ID, not necessarily the profile's display name.

The stable/profile paths follow Microsoft's documented user-settings directories and its source places `chatLanguageModels.json` in the profile directory. The Insiders rows apply the usual separate product data-directory convention. Custom `--user-data-dir`, portable installations, Linux `XDG_CONFIG_HOME`, and sandboxed packages can relocate these directories. Treat paths as discovery hints, not permission to create a missing file. [Microsoft settings locations](https://code.visualstudio.com/docs/configure/settings), [Microsoft profile resource implementation](https://github.com/microsoft/vscode/blob/main/src/vs/platform/userDataProfile/common/userDataProfile.ts)

To confirm the active file, use the same VS Code window/profile where the endpoint was created. Run **Chat: Manage Language Models**, then use the existing Custom Endpoint's configuration/edit control to open its JSON. Read the full path from the editor tab's **Copy Path** action and record it before editing. UI labels vary by version; use that version's existing-provider configuration action rather than adding another endpoint merely to locate the file.

For Remote SSH, WSL, containers or a browser-hosted editor, establish whether the opened resource belongs to the desktop client or the remote server. Connecting from Windows to thor-2 does not by itself move this profile file to Linux. Server-backed installations may keep user data under `~/.vscode-server/data/User/` or `~/.vscode-server-insiders/data/User/`, but do not assume a `chatLanguageModels.json` there is active: the resource opened by the provider UI and the installed version determine its location. Preserve that resource's credential scope. Do not put this user configuration in the repository's `.vscode/` directory or copy remote secret references into a local profile.

## Existing endpoint and credential boundary

First add a Custom Endpoint and store the key through VS Code's credential UI in the target profile/remote environment. Confirm an existing secret input reference without resolving its value, and preserve it verbatim. `REUSE_EXISTING_REFERENCE` below is a nonfunctional placeholder. Preserve unrelated providers and keep backups local and out of Git.

## Required selector configuration

Use one provider with one model and select reasoning through VS Code's native Thinking Effort submenu. The model-level fields `thinking`, `supportsReasoningEffort`, and `reasoningEffortFormat` shown below are mandatory for this recipe. Microsoft documents that the effort list enables the picker and `chat-completions` forwards its selection as a top-level `reasoning_effort` string. [VS Code model configuration](https://code.visualstudio.com/docs/agent-customization/language-models)

```json
[
  {
    "name": "Cerebras",
    "vendor": "customendpoint",
    "apiKey": "REUSE_EXISTING_REFERENCE",
    "apiType": "chat-completions",
    "models": [
      {
        "id": "qwen-3.8-27b",
        "name": "Cerebras Qwen 3.8 27B",
        "url": "https://api.cerebras.ai/v1/chat/completions",
        "toolCalling": true,
        "vision": true,
        "thinking": true,
        "contextWindow": 131072,
        "maxOutputTokens": 40960,
        "supportsReasoningEffort": ["none", "low", "medium", "high"],
        "reasoningEffortFormat": "chat-completions"
      }
    ]
  }
]
```

The capability flags and budgets reflect the operator's supplied configuration, not independently verified account entitlements. Verify tools, image inputs and reasoning support before advertising them. `contextWindow` is the combined input/output budget; VS Code derives 90112 input tokens from 131072 total minus 40960 output. If output changes, recompute the input allowance and verify provider/account limits. Preserve approved operating caps instead of silently enlarging them.

## Reasoning and version compatibility

Cerebras documents `none`, `low`, `medium`, and `high` for `qwen-3.8-27b`. `none` disables reasoning; `high` is the default and maps to Qwen's native `xhigh` mode. Reasoning tokens consume the completion allowance; effort does not guarantee a fixed token count. [Cerebras reasoning contract](https://inference-docs.cerebras.ai/capabilities/reasoning)

Select the model, open the arrow beside its name in the model picker, and choose Thinking Effort. Start with medium for ordinary interactive work; select other levels according to task needs and measured results. VS Code remembers effort per session and uses the last selected effort for that model in new conversations. Confirm the value in existing conversations too. [Microsoft picker behavior](https://code.visualstudio.com/docs/agent-customization/language-models#configure-thinking-effort)

Remove conflicting fixed `modelOptions.reasoning_effort` or legacy `requestOptions.extraBody.reasoning_effort` settings from the selected entry when adopting the selector. Do not infer forwarding from JSON presence alone. Verify the installed schema and redacted outgoing request. Stop if the selector is missing or its selected value is not forwarded; report the version incompatibility.

## Verification and rollback

Parse JSON and check a single intended provider/model, unchanged API model ID and URL, preserved credential reference, all required selector fields, valid budget arithmetic, and preservation of unrelated entries. A host bootstrap implementing this recipe must patch only the operator-selected entry and check these invariants idempotently.

Verify all four choices appear and send bounded sanitized chats for each. Inspect only redacted metadata proving `model=qwen-3.8-27b` and the selected `reasoning_effort`; never retain keys, authorization headers or private prompts. Include a tool-use fixture when Agent mode is intended. Record failures, truncation and usage as available. Compare representative tasks using elapsed time, time to first token where available, token usage and task acceptance. Bound retries and completion budgets; do not escalate effort automatically.

Label configuration checks separately from live request and performance evidence. On failure, restore the affected entry from the local backup, preserve unrelated intervening edits, and recheck the original endpoint. Do not delete stored secrets or change credentials during rollback.
