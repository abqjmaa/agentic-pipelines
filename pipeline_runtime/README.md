# pipeline_runtime

This directory owns pipeline runtime assets.

## Source inventory

- `__init__.py`: Local, resumable pipeline runtime primitives.
- `api.py`: The sole Ollama-compatible inference boundary for pipeline stages.
- `config.py`: Validated, local-only configuration for the shared inference primitive.
- `definition.py`: Strict schema-v2 loading for a host-owned pipeline definition.
- `evidence.py`: Stable public evidence interface composed from focused evidence modules.
- `package.py`: Validation for reviewable, non-running pipeline packages.
- `packets.py`: Deterministic source provenance and complete model-packet accounting.
- `prompts.py`: Versioned prompt loading, minimal-context rendering, and output validation.
- `redaction.py`: Redact configured literal secrets before evidence leaves process memory.
- `rejection_evidence.py`: Durable rejected-candidate and human-readable run evidence.
- `run_evidence.py`: Assemble structured run metrics and readable Markdown narratives.
- `runner.py`: Bounded resumable orchestration composed from focused runner components.
- `runner_candidates.py`: Candidate processing, rejected evidence and validated promotion.
- `runner_inference.py`: Bounded inference sessions, validation, repair and semantic review.
- `runner_io.py`: Atomic artifact writes and stable file identities for runner components.
- `runner_reports.py`: Structured run reports, human narratives and advisory cohort analysis.
- `state.py`: Transactional SQLite locks, attempts, evidence and recovery queries.
- `state_common.py`: Shared SQLite schema version, errors and UTC timestamps.
- `state_schema.py`: Versioned SQLite schema creation and additive migrations.
- `thread_capture.py`: Atomic, redacted evidence records for each local-inference call.
- `validators.py`: Deterministic, goal-specific candidate validation with stable evidence codes.
