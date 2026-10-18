# VS Code Cerebras reasoning presets

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

The operator first adds a Custom Endpoint and stores the key through VS Code's credential UI in the target profile/remote environment. The starter with blank model fields is a template to optimize after that step; it is not evidence that secret storage exists. Confirm an existing `${input:chat.lm.secret.…}` reference without resolving its value. Reuse that exact reference across the three provider entries below. `REUSE_EXISTING_REFERENCE` is deliberately a nonfunctional placeholder, never a secret ID to install.

Provider and model display names use `cerebras-qwen3.8:27b-<effort>`, following the readable model/tag style of local aliases while identifying the cloud provider and reasoning choice. These are not Ollama models or hostname/context aliases. Each provider contains one model because all three requests must send the same server model ID; distinct provider names separate their configuration groups. Preserve unrelated entries in the surrounding array. If an existing alias has conflicting settings, resolve the conflict rather than append a second copy.

## Current documented configuration

VS Code documents model-level `modelOptions` for request parameters and `contextWindow` as the total input/output budget. The following entries use that contract. [VS Code model configuration](https://code.visualstudio.com/docs/agent-customization/language-models)

```json
[
  {
    "name": "cerebras-qwen3.8:27b-low",
    "vendor": "customendpoint",
    "apiKey": "REUSE_EXISTING_REFERENCE",
    "apiType": "chat-completions",
    "models": [
      {
        "id": "qwen-3.8-27b",
        "name": "cerebras-qwen3.8:27b-low",
        "url": "https://api.cerebras.ai/v1/chat/completions",
        "toolCalling": true,
        "vision": true,
        "thinking": true,
        "contextWindow": 128144,
        "maxInputTokens": 112144,
        "maxOutputTokens": 16000,
        "modelOptions": { "reasoning_effort": "low" }
      }
    ]
  },
  {
    "name": "cerebras-qwen3.8:27b-medium",
    "vendor": "customendpoint",
    "apiKey": "REUSE_EXISTING_REFERENCE",
    "apiType": "chat-completions",
    "models": [
      {
        "id": "qwen-3.8-27b",
        "name": "cerebras-qwen3.8:27b-medium",
        "url": "https://api.cerebras.ai/v1/chat/completions",
        "toolCalling": true,
        "vision": true,
        "thinking": true,
        "contextWindow": 128144,
        "maxInputTokens": 112144,
        "maxOutputTokens": 16000,
        "modelOptions": { "reasoning_effort": "medium" }
      }
    ]
  },
  {
    "name": "cerebras-qwen3.8:27b-high",
    "vendor": "customendpoint",
    "apiKey": "REUSE_EXISTING_REFERENCE",
    "apiType": "chat-completions",
    "models": [
      {
        "id": "qwen-3.8-27b",
        "name": "cerebras-qwen3.8:27b-high",
        "url": "https://api.cerebras.ai/v1/chat/completions",
        "toolCalling": true,
        "vision": true,
        "thinking": true,
        "contextWindow": 128144,
        "maxInputTokens": 112144,
        "maxOutputTokens": 16000,
        "modelOptions": { "reasoning_effort": "high" }
      }
    ]
  }
]
```

The capability flags preserve the operator's supplied model configuration; verify tools, image inputs and reasoning rendering against the actual account/model before advertising those capabilities. The requested 128144 is an operating cap, not a claim of the provider's published maximum. Confirm account/model support first. With the starter's 16000-token output reserve, input is 112144; never combine 128144 input tokens with an additional 16000 output tokens under this cap. If changing output reserve, recompute input to retain the same total.

## Reasoning and version compatibility

Cerebras documents `low`, `medium` and `high` for this API model, with `high` as the default and mapped to Qwen's native `xhigh` mode. Reasoning consumes the completion allowance, and effort does not guarantee a fixed token count. Explicit effort prevents an omitted value from selecting high. [Cerebras reasoning contract](https://inference-docs.cerebras.ai/capabilities/reasoning)

Start with medium as the operator-requested interactive choice; use low for tasks that pass with less reasoning and high when measured answer fitness warrants it. Select the intended preset explicitly in new and existing conversations; listing medium does not set a global editor default.

The supplied Thor-2 configuration uses provider-level `requestOptions.extraBody.reasoning_effort`. Its presence in JSON does not prove that the installed extension forwards it. Current Microsoft source passes model-level `modelOptions` to the endpoint. Inspect the installed schema/source and the redacted outgoing body; use the old field only if that version demonstrably supports it. Do not combine competing effort settings or allow a picker/session override to contradict a fixed alias. If aliases collapse in the picker or an override wins, stop and report the version incompatibility. [Microsoft Custom Endpoint implementation](https://github.com/microsoft/vscode/blob/main/extensions/copilot/src/extension/byok/vscode-node/customEndpointProvider.ts)

## Verification and rollback

Before saving, parse JSON, confirm three unique provider/model display names, unchanged API model IDs and URLs, copied credential references, correct effort and budget sums, and preservation of every unrelated provider. Keep backups local and out of Git. A host bootstrap implementing this recipe must patch only the operator-selected entry and check the same invariants idempotently.

After saving, verify all three presets appear and send bounded sanitized chats in separate sessions. Inspect only redacted metadata proving `model=qwen-3.8-27b` and the selected `reasoning_effort`; do not retain keys, authorization headers or private prompts. Include a tool-use fixture when Agent mode is intended. Record failure, truncation and usage as available. Compare the same representative task across presets using elapsed time, time to first token where available, token usage and task acceptance. Bound retries and completion budgets; no automatic escalation to high or unsupported parameters.

Configuration-only verification must be labeled separately from live request or performance evidence. On failure, restore the affected provider entries from the local backup, preserve unrelated intervening edits, and recheck the original endpoint. Do not delete the stored secret or change credentials as part of rollback.
