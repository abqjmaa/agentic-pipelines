
## Cerebras reasoning preset playbook

User requested low/medium/high Cerebras Qwen 3.8 27B display aliases at a 128144-token total context, requiring prior user-created Custom Endpoint setup and stored credentials. Added and routed the concise playbook plus sanitized reference with three entries preserving the existing secret reference. Current VS Code documentation/source uses modelOptions.reasoning_effort; supplied Thor-2 requestOptions.extraBody is version-dependent and must be verified rather than assumed. Preserve API model ID qwen-3.8-27b; reserve the starter output budget of 16000, leaving 112144 input. Medium is the recommended operator choice, with actual request metadata and measured fitness required before performance claims.

Plan: plans/past/2026-10-13-10-18-18_cerebras-reasoning-presets.md, items 1.1-2.2 completed. Primary Cerebras reasoning and Microsoft configuration/implementation sources checked. JSON/name/effort/budget checks pass; router/documentation suites 18/18 pass. Existing playbook-size check fails on the unchanged 921-word Ollama playbook; the new playbook passes its size constraint. No installed configuration, key storage, runtime behavior or live calls changed. Parent ROADMAP and maturity map record the editor-documentation boundary; runtime implementation status is unaffected.

### Cerebras configuration file locations

User requested likely Windows/Linux chatLanguageModels.json paths. Added default/named profile and stable/Insiders path table, CJ/Thor examples, portable/custom/XDG relocation caveats, Remote SSH client-versus-server ownership guidance and active-path confirmation through the existing provider UI. Microsoft settings locations/profile source checked. Plan item 3 completed and re-archived; 18 routing/documentation tests pass, new playbook remains under 350 words. No installed configuration changes or delivery/runtime maturity changes.
